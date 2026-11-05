"""Run the compiled exporter and merge only document-local derived records."""

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from homalg import NODES_JSON_GENERATOR
from homalg.headers import code_only, imports_of, parse_header
from homalg.io import atomic_write, json_text
from homalg.repository import documents, node_paths
from homalg.schemas import SchemaStore, load_yaml

_workspace_locks = threading.local()


def assert_workspace_lock(repo: Path) -> None:
    """Fail closed if the held cooperative lock or its directory was replaced."""
    path = repo.resolve() / ".archon-horizon/cache/checks/workspace.lock"
    record = getattr(_workspace_locks, "held", {}).get((os.getpid(), path))
    if record is None:
        raise ValueError("The workspace lock must be held for this operation")
    try:
        current, parent = path.stat(), path.parent.stat()
        valid = (
            not path.is_symlink()
            and not path.parent.is_symlink()
            and (current.st_dev, current.st_ino) == record[0]
            and (parent.st_dev, parent.st_ino) == record[1]
        )
    except OSError:
        valid = False
    if not valid:
        raise ValueError("Workspace lock identity changed; stop concurrent work and retry")


class ExternalToolError(RuntimeError):
    """A failed Lake/exporter invocation, retaining the diagnostics and failed rule."""

    def __init__(self, command: list[str], output: str, returncode: int = 1):
        self.command = command
        self.output = output
        self.returncode = returncode
        self.rule = "decl-unique" if "environment already contains" in output else "lean-build"
        super().__init__(f"{' '.join(command)} exited with status {returncode}:\n{output.strip()}")


@contextmanager
def workspace_lock(repo: Path) -> Iterator[None]:
    """Serialize builds and exports; nesting in the same process/thread is safe.

    A reviewer can hold the lock through export and header registration. Other
    threads/processes still acquire a separate flock and wait for the whole transaction.
    Include the pid so a fork cannot accidentally inherit the reentrancy exemption.
    """
    path = repo.resolve() / ".archon-horizon/cache/checks/workspace.lock"
    held = getattr(_workspace_locks, "held", {})
    key = (os.getpid(), path)
    if key in held:
        assert_workspace_lock(repo)
        yield
        assert_workspace_lock(repo)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        _workspace_locks.held = held
        identity, parent = os.fstat(stream.fileno()), path.parent.stat()
        held[key] = ((identity.st_dev, identity.st_ino), (parent.st_dev, parent.st_ino))
        try:
            assert_workspace_lock(repo)
            yield
            assert_workspace_lock(repo)
        finally:
            del held[key]
            fcntl.flock(stream, fcntl.LOCK_UN)


def file_fingerprint(path: Path) -> dict[str, Any]:
    """Bind bytes and identity, detecting an edit even when the old bytes are restored."""
    before = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError(f"Input changed while reading: {path}")
    return {"sha256": digest, **{key: getattr(after, key) for key in fields}}


def compilation_inputs(repo: Path) -> dict[str, Any]:
    """Fingerprint build inputs, including local dependency sources and tool selection.

    Generated build artifacts are excluded. This is an input guard, never an export
    cache: every caller still performs a fresh Lake build/export. Package sources,
    local path dependencies and explicit LEAN_PATH roots are scanned conservatively.
    """
    repo = repo.resolve()
    paths = set(repo.glob("*.lean"))
    fixed = ("lean-toolchain", "lakefile.toml", "lake-manifest.json", "tools/uv.lock")
    paths.update(repo / name for name in fixed if (repo / name).is_file())
    roots = [repo / name for name in ("HomAlg", "HomAlgExport", "schema", "tools/homalg")]
    manifest = repo / "lake-manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text())
        packages = repo / data.get("packagesDir", ".lake/packages")
        for package in data.get("packages", []):
            roots.append(
                repo / package["dir"]
                if package.get("type") == "path"
                else packages / package["name"]
            )
    else:
        roots.append(repo / ".lake/packages")
    for name in ("LEAN_PATH", "LEAN_SRC_PATH"):
        roots.extend(repo / item for item in os.environ.get(name, "").split(os.pathsep) if item)
    visited = set()
    for root in roots:
        for directory, children, files in os.walk(root, followlinks=True):
            resolved = Path(directory).resolve()
            if resolved in visited:
                children.clear()
                continue
            visited.add(resolved)
            children[:] = [
                name for name in children if name not in {".git", ".lake", "__pycache__"}
            ]
            for name in files:
                if name.endswith((".lean", ".json", ".toml", ".py")) or name == "lean-toolchain":
                    paths.add(Path(directory) / name)
    paths.update((repo / "literature").glob("*/document.yaml"))
    policy = repo / "horizon/review-policy.yaml"
    if policy.exists():
        paths.add(policy)
    environment = {
        key: os.environ.get(key)
        for key in (
            "PATH",
            "ELAN_TOOLCHAIN",
            "ELAN_HOME",
            "LEAN_PATH",
            "LEAN_SRC_PATH",
            "LAKE_HOME",
        )
    }
    executables = {}
    search_path = os.pathsep.join(str(repo / item) for item in os.get_exec_path())
    for name in ("lake", "lean"):
        found = shutil.which(name, path=search_path)
        executables[name] = str(Path(found).resolve()) if found else None
        if found:
            paths.add(Path(found).resolve())
    pin = repo / "lean-toolchain"
    selected = os.environ.get("ELAN_TOOLCHAIN") or (pin.read_text().strip() if pin.exists() else "")
    elan = Path(os.environ.get("ELAN_HOME", str(Path.home() / ".elan")))
    toolchain = elan / "toolchains" / selected.replace("/", "--").replace(":", "---")
    for name in ("lake", "lean"):
        binary = toolchain / "bin" / name
        if binary.is_file():
            paths.add(binary)
    return {
        "files": {str(path.resolve()): file_fingerprint(path) for path in sorted(paths)},
        "environment": environment,
        "executables": executables,
    }


def run_tool(repo: Path, command: list[str]) -> str:
    """Capture stdout for machine processing; failures retain both diagnostic streams."""
    try:
        result = subprocess.run(
            command, cwd=repo, capture_output=True, text=True, check=False, timeout=3600
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ExternalToolError(command, str(error)) from error
    if result.returncode:
        raise ExternalToolError(command, result.stdout + result.stderr, result.returncode)
    return result.stdout


def module_list(repo: Path, keys: list[str]) -> list[str]:
    """Include document roots and every node, including orphan auxiliaries and citations."""
    modules = {
        ".".join(path.relative_to(repo).with_suffix("").parts) for path in node_paths(repo, keys)
    }
    modules.update(f"HomAlg.{key}" for key in keys if (repo / "HomAlg" / f"{key}.lean").exists())
    return sorted(modules)


def check_constants(repo: Path, keys: list[str], schemas: SchemaStore) -> list[str]:
    """Collect names whose existence is a prerequisite for fidelity comparison rules."""
    names: set[str] = set()
    for key in keys:
        path = repo / "literature" / key / "document.yaml"
        document = load_yaml(path.read_text(encoding="utf-8"))
        errors = schemas.validate(document, "document.schema.json")
        if errors:
            raise ValueError(f"{path}: {errors[0].message}")
        for entry in document["foundations"]:
            names.update(entry["mathlib"])
    for path in node_paths(repo, keys):
        header = parse_header(path.read_text(encoding="utf-8"))
        errors = schemas.validate(header.metadata, "node-header.strict.schema.json")
        if errors:
            raise ValueError(f"{path}:{header.yaml_line}: {errors[0].message}")
        names.update(header.metadata.get("mathlib", {}).get("decls", []))
    return sorted(names)


def declaration_map(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Index validated export records, rejecting duplicate modules or declaration names."""
    modules = {}
    all_names = set()
    for module in raw["modules"]:
        name = module["module"]
        if name in modules:
            raise ValueError(f"Duplicate exported module: {name}")
        records = {}
        for declaration in module["decls"]:
            identifier = declaration["name"]
            if identifier in all_names:
                raise ValueError(f"Duplicate exported declaration: {identifier}")
            all_names.add(identifier)
            records[identifier] = declaration
        modules[name] = records
    return modules


def local_derived(
    path: str, content: bytes, header: dict[str, Any], declarations: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Derive stable per-file information without leaking import-closure axioms or sorry."""
    text = content.decode("utf-8")
    names = header.get("decls", [])
    found = [declarations[name] for name in names if name in declarations]
    if not names or len(found) != len(names):
        status = "planned"
    elif any(declaration["direct_sorry"] for declaration in found):
        status = "stated"
    else:
        status = "proved"
    decl_info = [
        {
            key: value
            for key, value in declaration.items()
            if key
            not in {
                "axioms",
                "transitive_sorry",
                "packaged_fields",
                "is_global_instance",
                "instance_type_uses_own_doc",
            }
        }
        | {"type_sha256": hashlib.sha256(declaration["type"].encode("utf-8")).hexdigest()}
        for declaration in found
    ]
    statement = set()
    proof = set()
    for declaration in found:
        statement.update(declaration["type_uses_nodes"])
        if declaration["is_prop"]:
            proof.update(declaration["value_uses_nodes"])
        else:
            statement.update(declaration["value_uses_nodes"])
    proof -= statement
    declared = {kind: sorted(set(header["deps"][kind])) for kind in ("statement", "proof")}
    imports = imports_of(text)
    return {
        "local_status": status,
        "decl_info": decl_info,
        "verified_deps": {"statement": sorted(statement), "proof": sorted(proof)},
        "declared_deps": declared,
        "deps_diff": {
            "declared_not_verified": {
                "statement": sorted(set(declared["statement"]) - statement),
                "proof": sorted(set(declared["proof"]) - statement - proof),
            },
            "verified_not_declared": sorted(
                (statement | proof) - set(declared["statement"]) - set(declared["proof"])
            ),
        },
        "imports": {
            "nodes": sorted(
                module.removeprefix("HomAlg.")
                for module in imports
                if module.startswith("HomAlg.") and module.count(".") == 2
            ),
            "mathlib": sorted(module for module in imports if module.startswith("Mathlib.")),
        },
        "sorry_count_text": len(re.findall(r"\bsorry\b", code_only(text))),
        "file": {
            "path": path,
            "lines": max(1, len(text.splitlines())),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    }


def merge_document(
    repo: Path,
    key: str,
    raw: dict[str, Any],
    modules: dict[str, dict[str, dict[str, Any]]],
    schemas: SchemaStore,
) -> dict[str, Any]:
    """Preserve authored records while replacing their local derived data (R7.5)."""
    target = repo / "literature" / key / "nodes.json"
    previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    if previous:
        errors = schemas.validate(previous, "nodes-file.schema.json")
        if errors or previous["doc_key"] != key:
            raise ValueError(f"Cannot preserve invalid authored records in {target}")
    old_nodes = {node["id"]: node for node in previous["nodes"]} if previous else {}
    if previous and len(old_nodes) != len(previous["nodes"]):
        raise ValueError(f"Duplicate node ids in {target}")
    nodes = []
    for path in node_paths(repo, [key]):
        content = path.read_bytes()
        header = parse_header(content.decode("utf-8"))
        errors = schemas.validate(header.metadata, "node-header.strict.schema.json")
        if errors:
            raise ValueError(f"{path}:{header.yaml_line}: {errors[0].message}")
        identifier = f"{key}.{path.stem}"
        if header.metadata["id"] != identifier or header.metadata["doc"] != key:
            raise ValueError(f"{path}: node id does not match its file")
        nodes.append(
            {
                "id": identifier,
                "authored": old_nodes.get(identifier, {}).get("authored", header.authored()),
                "derived": local_derived(
                    path.relative_to(repo).as_posix(),
                    content,
                    header.metadata,
                    modules.get(f"HomAlg.{identifier}", {}),
                ),
            }
        )
    result = {
        "schema_version": 1,
        "generator": {"name": "homalg", "version": str(NODES_JSON_GENERATOR)},
        "doc_key": key,
        "lean": {"toolchain": raw["toolchain"], "mathlib_rev": raw["mathlib_rev"]},
        "nodes": nodes,
    }
    errors = schemas.validate(result, "nodes-file.schema.json")
    if errors:
        raise ValueError(f"Cannot merge Lean export for {key}: {errors[0].message}")
    return result


def export_lean(
    repo: Path, doc: str | None = None, out: Path | None = None, *, merge: bool = True
) -> dict[str, Any]:
    """Build selected modules, export authoritative JSON, and merge local derived records.

    ``doc=None`` exports every registered document. The raw JSON retains axioms,
    transitive sorry and packaging evidence; committed node files exclude them.
    ``ExternalToolError`` identifies failed builds/imports; ``ValueError`` identifies
    malformed input, duplicate declarations, invalid exports or concurrent edits.
    All generated JSON files are replaced atomically after validation succeeds.
    ``merge=False`` leaves committed node files untouched for validation/freshness checks.
    """
    repo = repo.resolve()
    suffix = f"-{doc}" if doc else ""
    target = out or Path(f"build/lean-export{suffix}.json")
    if not target.is_absolute():
        target = repo / target
    with workspace_lock(repo):
        before = compilation_inputs(repo)
        keys = documents(repo, (doc,) if doc else ())
        schemas = SchemaStore(repo / "schema")
        modules_file = repo / f"build/modules{suffix}.txt"
        modules = module_list(repo, keys)
        constants_file = repo / f"build/check-constants{suffix}.txt"
        atomic_write(
            constants_file, "".join(f"{name}\n" for name in check_constants(repo, keys, schemas))
        )
        atomic_write(modules_file, "".join(f"{module}\n" for module in modules))
        # An editor can write despite the cooperative build lock. Refuse to label an
        # export with source hashes that differ from the sources its build consumed.
        run_tool(repo, ["lake", "build", "homalg-export", *modules])
        output = run_tool(
            repo,
            [
                "lake",
                "exe",
                "homalg-export",
                "--modules",
                str(modules_file),
                "--check-constants",
                str(constants_file),
                "--prefix",
                f"HomAlg.{doc}" if doc else "HomAlg",
            ],
        )
        try:
            raw = json.loads(output)
        except json.JSONDecodeError as error:
            raise ExternalToolError(["homalg-export"], f"Invalid JSON output: {error}") from error
        errors = schemas.validate(raw, "lean-export.schema.json")
        if errors:
            raise ValueError(f"Invalid Lean export: {errors[0].message}")
        if compilation_inputs(repo) != before:
            raise ValueError("Lean sources changed or build inputs changed while exporting; retry")
        declarations = declaration_map(raw)
        missing = set(modules) - declarations.keys()
        if missing:
            raise ValueError(f"Lean export omitted requested modules: {', '.join(sorted(missing))}")
        merged = (
            [(key, merge_document(repo, key, raw, declarations, schemas)) for key in keys]
            if merge
            else []
        )
        if compilation_inputs(repo) != before:
            raise ValueError("Lean sources changed or build inputs changed while merging; retry")
        assert_workspace_lock(repo)
        atomic_write(target, json_text(raw))
        for key, data in merged:
            atomic_write(repo / "literature" / key / "nodes.json", json_text(data))
    return raw
