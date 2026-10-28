"""Authored-source, identity, proof-route metadata and repository-policy checks."""

import hashlib
import json
import os
import re
import subprocess
import tomllib
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import networkx as nx

from homalg.checks.context import Context, Finding
from homalg.claims import effective_expiry, instant, load_status_history
from homalg.headers import code_only, imports_of
from homalg.leantext import DECL_KINDS
from homalg.relations import merged_ids

LOCAL_ID = re.compile(r"[A-Z][A-Za-z0-9]*(_[A-Za-z0-9]+)*")
DOC_KEY = re.compile(r"[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*")
RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", re.I)
THEOREM_TYPES = {"theorem", "lemma", "proposition", "corollary", "example", "exercise"}


def finding(
    rule: str, path: str, message: str, *, severity: str = "error", line: int | None = None
) -> Finding:
    """Create source diagnostics with consistent rule/severity semantics."""
    return Finding(rule, severity, path, message, line)


def id_grammar(ctx: Context) -> list[Finding]:
    """Check stable portable names, case-folded uniqueness and retired tombstones."""
    result = []
    docs = [path.parent.name for path in (ctx.repo / "literature").glob("*/document.yaml")]
    for key, count in Counter(name.casefold() for name in docs).items():
        if count > 1:
            result.append(
                finding("id-grammar", "literature", f"Case-insensitive duplicate DocKey: {key}")
            )
    for doc in docs:
        if not DOC_KEY.fullmatch(doc):
            result.append(
                finding("id-grammar", f"literature/{doc}/document.yaml", "Invalid DocKey")
            )
        locals_ = [path.stem for path in (ctx.repo / "HomAlg" / doc).glob("*.lean")]
        for local, count in Counter(name.casefold() for name in locals_).items():
            if count > 1:
                result.append(
                    finding(
                        "id-grammar",
                        f"HomAlg/{doc}",
                        f"Case-insensitive duplicate LocalId: {local}",
                    )
                )
    for path in ctx.sources:
        local = Path(path).stem
        if not LOCAL_ID.fullmatch(local) or RESERVED.fullmatch(local):
            result.append(finding("id-grammar", path, "Invalid or filesystem-reserved LocalId"))
        identifier = ".".join(Path(path).with_suffix("").parts[1:])
        if identifier in ctx.retired:
            result.append(finding("id-grammar", path, "Retired node ids may never be reused"))
    return result


def namespace(ctx: Context) -> list[Finding]:
    """All source declarations belong to the document namespace, including helpers."""
    return [
        finding(
            "namespace",
            path,
            f"Declaration {command.name or '(anonymous)'} is outside "
            f"namespace {header.metadata['doc']}",
            line=command.line,
        )
        for path, header in ctx.valid_headers.items()
        for command in ctx.commands.get(path, [])
        if command.kind in DECL_KINDS
        and (
            not command.namespace
            or command.namespace.split(".")[0] != header.metadata["doc"]
            or command.raw_name.startswith("_root_.")
        )
    ]


def lean_style(ctx: Context) -> list[Finding]:
    """Check namespace safety, scoped syntax/attributes, docstrings and finite resource limits."""
    result = []
    all_decls = {
        command.name for commands in ctx.commands.values() for command in commands if command.name
    }
    by_node = ctx.node_headers()
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        doc = metadata["doc"]
        text = ctx.sources[path]
        masked = code_only(text)
        commands = ctx.commands.get(path, [])
        declarations = [command for command in commands if command.kind in DECL_KINDS]

        def add(message: str, line: int | None = None, source_path: str = path) -> None:
            result.append(finding("lean-style", source_path, message, line=line))

        for module in imports_of(text):
            if module == "Mathlib":
                add("Import specific Mathlib modules, not the umbrella module")
            if module == "HomAlg" or (module.startswith("HomAlg.") and module.count(".") == 1):
                add("Nodes may not import library/document root modules")
        if re.search(r"(?m)^\s*export\b", masked):
            add("The export command is forbidden in document nodes")
        deviations = {item["kind"] for item in metadata["fidelity"].get("deviations", [])}
        for command in declarations:
            modifiers = command.modifiers.split()
            if "private" in modifiers:
                add("Private declarations cannot participate in statement locks", command.line)
            if command.raw_name.startswith("_root_."):
                add("A declaration may not escape through _root_", command.line)
            if {"unsafe", "partial"} & set(modifiers) and "algorithmic" not in deviations:
                add("Unsafe/partial declarations require an algorithmic deviation", command.line)
            if not command.docstring:
                add(
                    f"Declaration {command.name or '(anonymous)'} requires a docstring",
                    command.line,
                )
        main = metadata.get("decls", [])
        if main:
            primary = next((command for command in declarations if command.name == main[0]), None)
            label = metadata["source"]["label"]
            if "aux" in metadata:
                parent = by_node.get(metadata["aux"]["parent"])
                parent_label = parent.metadata["source"]["label"] if parent else ""
                label = (
                    "Bridge for " if metadata["aux"]["kind"] == "bridge" else "Auxiliary to "
                ) + parent_label
            if primary and not primary.docstring.startswith(f"**{label}**"):
                add(f"Primary docstring must start with **{label}**", primary.line)
        if declarations and not re.search(rf"\bend\s+{re.escape(doc)}\s*$", masked):
            add(f"A node with declarations must end with end {doc}")
        for match in re.finditer(r"(?m)^\s*open\s+(?!scoped\b)([^\n]+)", masked):
            words = re.findall(r"[A-Za-z][A-Za-z0-9]*", match.group(1))
            foreign = [word for word in words if word in ctx.all_docs and word != doc]
            if foreign:
                add(f"Use fully qualified cross-document names instead of open {foreign[0]}")
        for command in commands:
            if command.kind != "other":
                continue
            body = command.text
            if re.match(r"(?:notation|infix[lr]?|prefix|postfix|macro|syntax|elab)\b", body):
                add("Syntax and notation declarations must be local or scoped", command.line)
            if re.match(r"attribute\s*\[", body) and not re.match(
                r"attribute\s*\[\s*(?:local|scoped)\b", body
            ):
                names = re.sub(r"^attribute\s*\[[^]]*\]\s*", "", body).split()
                for name in names:
                    candidates = {f"{command.namespace}.{name}", name}
                    if not any(
                        candidate in all_decls and candidate.startswith(f"{doc}.")
                        for candidate in candidates
                    ):
                        add(
                            f"Attributes on external declarations must be local or scoped: {name}",
                            command.line,
                        )
            limit = re.search(
                r"set_option\s+(?:maxHeartbeats|synthInstance.maxHeartbeats)\s+(\d+)", body
            )
            if limit and (int(limit.group(1)) == 0 or int(limit.group(1)) > 400000):
                if not header.sections.get("Formalization notes", "").strip():
                    add(
                        "An unlimited/large heartbeat budget needs formalization notes",
                        command.line,
                    )
    return result


def sorry_named(ctx: Context) -> list[Finding]:
    """Every sorry/admit token must lie inside a documented named theorem or lemma."""
    result = []
    for path, source in ctx.sources.items():
        if path not in ctx.commands:
            continue
        masked = code_only(source)
        commands = ctx.commands.get(path, [])
        for token in re.finditer(r"(?<![\w.'])(?:sorry|admit)(?![\w'])", masked):
            owner = next(
                (command for command in commands if command.start <= token.start() < command.end),
                None,
            )
            if (
                owner is None
                or owner.kind not in {"theorem", "lemma"}
                or not owner.name
                or not owner.docstring
            ):
                result.append(
                    finding(
                        "sorry-named",
                        path,
                        "Every sorry/admit must belong to a documented named theorem or lemma",
                        line=source.count("\n", 0, token.start()) + 1,
                    )
                )
    return result


def decl_unique(ctx: Context) -> list[Finding]:
    """The text layer catches duplicate names before an aggregate module import."""
    locations: dict[str, list[tuple[str, int]]] = {}
    for path, commands in ctx.commands.items():
        for command in commands:
            if command.name:
                locations.setdefault(command.name, []).append((path, command.line))
    return [
        finding(
            "decl-unique",
            path,
            f"Duplicate declaration {name}: " + ", ".join(p for p, _ in locations[name]),
            line=line,
        )
        for name in locations
        if len(locations[name]) > 1
        for path, line in locations[name]
        if path in ctx.sources
    ]


def aux_parent(ctx: Context) -> list[Finding]:
    """Auxiliary and bridge prefixes are exactly the nodes carrying parent metadata."""
    result = []
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        local = metadata["id"].split(".", 1)[1]
        auxiliary = local.startswith(("Aux_", "Bridge_"))
        aux = metadata.get("aux")
        if auxiliary != bool(aux):
            result.append(
                finding("aux-parent", path, "Aux_/Bridge_ prefixes and aux metadata must agree")
            )
        if aux and (local.startswith("Bridge_") != (aux["kind"] == "bridge")):
            result.append(
                finding("aux-parent", path, "Bridge_ requires aux.kind bridge and vice versa")
            )
        if aux and (
            aux["parent"] not in ctx.existing_nodes
            or aux["parent"].split(".")[0] != metadata["doc"]
            or aux["parent"] == metadata["id"]
        ):
            result.append(
                finding(
                    "aux-parent",
                    path,
                    "Auxiliary parent must be a different existing node in this document",
                )
            )
    return result


def cited_source(ctx: Context) -> list[Finding]:
    """Citations preserve a valid source and never become auxiliary nodes."""
    result = []
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        cited = metadata.get("cited")
        if metadata["id"].split(".")[1].startswith("Cited_") != bool(cited):
            result.append(
                finding("cited-source", path, "Cited_ prefixes and cited metadata must agree")
            )
        if cited and "aux" in metadata:
            result.append(finding("cited-source", path, "Cited nodes are not auxiliary nodes"))
        if (
            cited
            and cited["source"]["kind"] == "document"
            and cited["source"]["doc"] not in ctx.all_docs
        ):
            result.append(finding("cited-source", path, "The cited document must be registered"))
        if cited and (not cited.get("used_at") or cited["used_at"] != metadata["source"]["pages"]):
            result.append(finding("cited-source", path, "cited.used_at must match source.pages"))
        if (
            cited
            and cited["formulation"] == "editorial"
            and not header.sections.get("Statement", "").startswith("[Editorial]")
        ):
            result.append(
                finding(
                    "cited-source", path, "Editorial cited statements must start with [Editorial]"
                )
            )
    return result


def cited_used(ctx: Context) -> list[Finding]:
    """Unused citation nodes are reviewable pruning candidates."""
    used = {
        dep
        for header in ctx.all_headers.values()
        for deps in header.metadata["deps"].values()
        for dep in deps
    }
    return [
        finding(
            "cited-used",
            path,
            "No node declares a dependency on this cited result",
            severity="warning",
        )
        for path, header in ctx.valid_headers.items()
        if "cited" in header.metadata and header.metadata["id"] not in used
    ]


def foundation_declared(ctx: Context) -> list[Finding]:
    """A foundation alias is allowed only inside this document's confirmed reviewed boundary."""
    from homalg.review_policy import agent_reviews_allowed, valid_agent_review

    result = []
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        if metadata["fidelity"]["status"] != "foundation":
            continue
        allowed = {
            name
            for entry in ctx.all_docs.get(metadata["doc"], {}).get("foundations", [])
            for name in entry["mathlib"]
        }
        mathlib = metadata.get("mathlib", {})
        if (
            mathlib.get("relation") != "same"
            or not set(mathlib.get("decls", [])) <= allowed
            or not mathlib.get("decls")
        ):
            result.append(
                finding(
                    "foundation-declared",
                    path,
                    "Foundation aliases require same counterparts declared in document.foundations",
                )
            )
        review = metadata["fidelity"].get("reviewed", {})
        if review.get("kind") != "human" and not (
            agent_reviews_allowed(ctx.repo) and valid_agent_review(review)
        ):
            result.append(
                finding(
                    "foundation-declared",
                    path,
                    "A foundation alias needs a human or authorized independent-agent lock",
                )
            )
        if any(command.kind not in {"abbrev", "other"} for command in ctx.commands.get(path, [])):
            result.append(
                finding(
                    "foundation-declared",
                    path,
                    "Foundation nodes may only recall notions with abbrev/notation/variable",
                )
            )
    return result


def deviation_justified(ctx: Context) -> list[Finding]:
    """Deviations require explicit reasons and an authorized review before a PR can merge."""
    from homalg.review_policy import agent_reviews_allowed, valid_agent_review

    result = []
    allowed = set(ctx.schemas.schemas["common.schema.json"]["$defs"]["DeviationKind"]["enum"])
    for path, header in ctx.valid_headers.items():
        fidelity = header.metadata["fidelity"]
        if fidelity["status"] != "deviates":
            continue
        if not fidelity.get("deviations") or any(
            item["kind"] not in allowed or not item["what"].strip() or not item["why"].strip()
            for item in fidelity.get("deviations", [])
        ):
            result.append(
                finding(
                    "deviation-justified",
                    path,
                    "Every deviation needs a recognized kind, what changed, and why",
                )
            )
        review = fidelity.get("reviewed", {})
        if (
            ctx.pr
            and review.get("kind") != "human"
            and not (agent_reviews_allowed(ctx.repo) and valid_agent_review(review))
        ):
            result.append(
                finding(
                    "deviation-justified",
                    path,
                    "Deviations need a human or authorized independent-agent lock before merge",
                )
            )
    return result


def graph_check(ctx: Context, *, documents: bool) -> list[Finding]:
    """Reject every dependency cycle, including planned nodes that have no imports."""
    graph = nx.DiGraph()
    for path, header in ctx.all_headers.items():
        identifier = header.metadata["id"]
        if documents:
            source = header.metadata["doc"]
            graph.add_node(source)
            for module in imports_of(ctx.all_sources[path]):
                if module.startswith("HomAlg.") and module.count(".") == 2:
                    target = module.split(".")[1]
                    if target != source:
                        graph.add_edge(source, target)
        else:
            graph.add_node(identifier)
            graph.add_edges_from(
                (identifier, target) for deps in header.metadata["deps"].values() for target in deps
            )
    rule = "doc-acyclic" if documents else "deps-acyclic"
    result = []
    for component in nx.strongly_connected_components(graph):
        if len(component) > 1 or any(graph.has_edge(node, node) for node in component):
            result.append(
                finding(rule, "HomAlg", "Dependency cycle: " + ", ".join(sorted(component)))
            )
    return result


def doc_import_direction(ctx: Context) -> list[Finding]:
    """Cross-document imports point to earlier documents unless explicitly exempted."""
    result = []

    def order(key: str) -> tuple[int, int, str]:
        doc = ctx.all_docs[key]
        return doc["year"], 0 if doc["type"] == "synthetic" else 1, key

    for path, header in ctx.valid_headers.items():
        key = header.metadata["doc"]
        if key not in ctx.all_docs:
            continue
        for module in imports_of(ctx.sources[path]):
            if not module.startswith("HomAlg.") or module.count(".") != 2:
                continue
            target = module.split(".")[1]
            if (
                target != key
                and target in ctx.all_docs
                and target not in ctx.all_docs[key].get("may_import", [])
                and order(target) >= order(key)
            ):
                result.append(
                    finding(
                        "doc-import-direction",
                        path,
                        f"Import {module} points forward in document order; "
                        "an owner-reviewed may_import exception is required",
                    )
                )
    return result


def label_unique(ctx: Context) -> list[Finding]:
    """Source labels are unique within each document and each inventory."""
    result = []
    grouped: dict[tuple[str, str], list[str]] = {}
    for path, header in ctx.all_headers.items():
        if "aux" not in header.metadata:
            grouped.setdefault(
                (header.metadata["doc"], header.metadata["source"]["label"]), []
            ).append(path)
    for (_, label), paths in grouped.items():
        if len(paths) > 1:
            result.extend(
                finding("label-unique", path, f"Repeated source label {label}: {', '.join(paths)}")
                for path in paths
                if path in ctx.sources
            )
    for key, inventory in ctx.inventories.items():
        counts = Counter(
            item["label"] for page in inventory["pages"].values() for item in page["items"]
        )
        for label, count in counts.items():
            if count > 1:
                result.append(
                    finding(
                        "label-unique",
                        f"literature/{key}/inventory.yaml",
                        f"Repeated inventory label: {label}",
                    )
                )
    return result


def inventory_valid(ctx: Context) -> list[Finding]:
    """Every inventory disposition points to an existing node in its document."""
    result = []
    for key, inventory in ctx.inventories.items():
        path = f"literature/{key}/inventory.yaml"
        if inventory["doc_key"] != key:
            result.append(
                finding("inventory-valid", path, "Inventory doc_key must match its directory")
            )
        for page in inventory["pages"].values():
            for item in page["items"]:
                if item["disposition"] in {"node", "informal"} and (
                    item["node"] not in ctx.existing_nodes or item["node"].split(".")[0] != key
                ):
                    result.append(
                        finding(
                            "inventory-valid",
                            path,
                            f"Missing inventory node in this document: {item['node']}",
                        )
                    )
    return result


def nodes_json_stale(ctx: Context) -> list[Finding]:
    """Fast source/toolchain freshness never pretends to replace a compiled export."""
    result = []
    toolchain = (ctx.repo / "lean-toolchain").read_text().strip()
    try:
        packages = json.loads((ctx.repo / "lake-manifest.json").read_text())["packages"]
        mathlib = next(item for item in packages if item["name"] == "mathlib")
        revision = mathlib.get("inputRev") or mathlib["rev"]
    except (OSError, ValueError, KeyError, StopIteration):
        config = tomllib.loads((ctx.repo / "lakefile.toml").read_text())
        revision = next(item["rev"] for item in config["require"] if item["name"] == "mathlib")
    for key in ctx.docs:
        records = ctx.nodes_files.get(key)
        stale = records is None or records.get("lean") != {
            "toolchain": toolchain,
            "mathlib_rev": revision,
        }
        nodes = {node["id"]: node for node in records.get("nodes", [])} if records else {}
        for path, header in ctx.valid_headers.items():
            if header.metadata["doc"] != key:
                continue
            derived = nodes.get(header.metadata["id"], {}).get("derived")
            if (
                derived is None
                or derived["file"]["sha256"]
                != hashlib.sha256(ctx.sources[path].encode()).hexdigest()
            ):
                stale = True
        if stale:
            result.append(
                Finding(
                    "nodes-json-stale",
                    "warning",
                    f"literature/{key}/nodes.json",
                    "stale: regenerate compiled local records",
                    fix=f"homalg export-lean --doc {key}",
                )
            )
    return result


def vocabulary(ctx: Context, *, concepts: bool) -> list[Finding]:
    """Distinguish unknown ids and stale aliases, respecting changed-header severity."""
    field = "concepts" if concepts else "tags"
    rule = "concepts-known" if concepts else "tags-known"
    known = {entry["id"]: entry for entry in ctx.taxonomy.get(field, {}).get(field, [])}
    result = []
    for path, header in ctx.valid_headers.items():
        values = (
            [value for group in header.metadata.get("concepts", {}).values() for value in group]
            if concepts
            else header.metadata["tags"]
        )
        for value in values:
            if value not in known:
                result.append(
                    finding(rule, path, f"Unknown {field} id: {value}", line=header.yaml_line)
                )
            elif known[value].get("merged_into"):
                changed = path in ctx.changed_paths
                result.append(
                    finding(
                        rule if changed else "taxonomy-merged",
                        path,
                        f"{value} was merged into {known[value]['merged_into']}; "
                        "run homalg taxonomy apply-merges",
                        severity="error" if changed else "warning",
                        line=header.yaml_line,
                    )
                )
    return result


def taxonomy_merge_cycle(ctx: Context) -> list[Finding]:
    """Alias chains and taxonomy parent hierarchies have existing, acyclic targets."""
    result = []
    for field in ("tags", "concepts"):
        entries = ctx.taxonomy.get(field, {}).get(field, [])
        path = f"taxonomy/{field}.yaml"
        try:
            merged_ids(entries)
        except ValueError as error:
            result.append(finding("taxonomy-merge-cycle", path, str(error)))
        known = {entry["id"] for entry in entries}
        graph = nx.DiGraph()
        for entry in entries:
            parents = (
                entry.get("parents", [])
                if field == "concepts"
                else ([entry["parent"]] if entry.get("parent") else [])
            )
            for parent in parents:
                if parent not in known:
                    result.append(
                        finding("taxonomy-merge-cycle", path, f"Missing parent: {parent}")
                    )
                graph.add_edge(entry["id"], parent)
        if not nx.is_directed_acyclic_graph(graph):
            result.append(
                finding("taxonomy-merge-cycle", path, "Taxonomy parent hierarchy has a cycle")
            )
    return result


def no_pdf(ctx: Context) -> list[Finding]:
    """Keep public source paths free of PDFs while permitting the ignored private archive."""
    ignored = {".git", ".lake", ".private", ".venv", "node_modules", "build", ".archon-horizon"}
    found = []
    for directory, children, files in os.walk(ctx.repo):
        children[:] = [name for name in children if name not in ignored]
        for name in files:
            if name.lower().endswith(".pdf"):
                found.append((Path(directory) / name).relative_to(ctx.repo).as_posix())
    # An ignored local private archive is allowed, but force-adding a PDF to Git
    # must be caught even when its path is under an otherwise excluded directory.
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ctx.repo, capture_output=True, text=True
    )
    if tracked.returncode == 0:
        found.extend(name for name in tracked.stdout.split("\0") if name.lower().endswith(".pdf"))
    return [
        finding("no-pdf", path, "PDFs belong only in the private literature archive")
        for path in sorted(set(found))
    ]


def out_of_scope(ctx: Context) -> list[Finding]:
    """Warn on newly added source items outside a contributor's declared chapter/section scope."""
    result = []
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        key = metadata["doc"]
        if key.startswith("Fixture") or path in ctx.base_sources:
            continue
        claims = ctx.claims.get(key, {}).get("claims", [])
        if not claims:
            continue
        current = instant(ctx.now or datetime.now(UTC))
        try:
            history = load_status_history(ctx.repo, key, schemas=ctx.schemas)
        except ValueError:
            history = []
        expiry = effective_expiry(
            claims[0],
            history,
            current,
            schemas=ctx.schemas,
            doc_key=key,
            grace_days=ctx.taxonomy.get("policy", {}).get("claim_activity_grace_days", 14),
        )
        if expiry <= current:
            continue
        scope = claims[0]["scope"]
        chapters, sections = scope["chapters"], scope["sections"]
        if (
            (chapters or sections)
            and metadata["source"].get("chapter") not in chapters
            and metadata["source"].get("section") not in sections
        ):
            result.append(
                finding(
                    "out-of-scope",
                    path,
                    "New node is outside the active claim's chapter/section scope",
                    severity="warning",
                )
            )
    return result


def file_size(ctx: Context) -> list[Finding]:
    """Large source nodes merit review before becoming a build bottleneck."""
    return [
        finding("file-size", path, "Node exceeds 2000 lines", severity="warning")
        for path, source in ctx.sources.items()
        if len(source.splitlines()) > 2000
    ]


def english_only(ctx: Context) -> list[Finding]:
    """Warn about non-English scripts while allowing mathematical Greek and source originals."""

    def foreign(text: str) -> bool:
        return any(
            unicodedata.category(char).startswith("L")
            and not any(script in unicodedata.name(char, "") for script in ("LATIN", "GREEK"))
            for char in text
            if ord(char) > 127
        )

    result = []
    for path, header in ctx.valid_headers.items():
        metadata = {
            key: value for key, value in header.metadata.items() if key not in {"title", "bibtex"}
        }
        text = (
            json.dumps(metadata, ensure_ascii=False)
            + "\n"
            + "\n".join(
                value for title, value in header.sections.items() if title != "Statement (original)"
            )
        )
        text += "\n" + "\n".join(
            command.name + " " + command.docstring for command in ctx.commands.get(path, [])
        )
        if foreign(text):
            result.append(
                finding(
                    "english-only",
                    path,
                    "Use English prose/identifiers outside the original-language statement",
                    severity="warning",
                )
            )
    return result
