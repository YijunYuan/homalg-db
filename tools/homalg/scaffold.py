"""Schema-checked, exclusive document and node scaffolding."""

import hashlib
import re
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata, read_document
from homalg.headers import THEOREM_KINDS, parse_header
from homalg.nodeio import node_path
from homalg.repository import DOC_KEY
from homalg.schemas import SchemaStore, load_yaml

RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", re.I)


def new_node(
    repo: Path,
    node_id: str,
    *,
    kind: str,
    tags: list[str],
    pages: list[int] | None = None,
    label: str | None = None,
    chapter: str | None = None,
    section: str | None = None,
    title: str | None = None,
    parent: str | None = None,
    aux_kind: str | None = None,
    reason: str | None = None,
    cited_kind: str | None = None,
    cited_ref: str | None = None,
    cited_doc: str | None = None,
    cited_locator: str | None = None,
    used_at: list[int] | None = None,
) -> Path:
    """Create one planned node atomically, rejecting id reuse and incomplete auxiliary metadata."""
    path = node_path(repo, node_id)
    key, local = node_id.split(".", 1)
    if RESERVED.fullmatch(local):
        raise ValueError(f"Reserved filesystem name: {local}")
    doc = read_document(repo, key)
    if doc.get("structure"):
        chapters = {item["chapter"]: item for item in doc["structure"]}
        if chapter not in chapters:
            raise ValueError("--chapter must identify an entry in document.structure")
        sections = chapters[chapter].get("sections", [])
        if sections and section not in {item["id"] for item in sections}:
            raise ValueError("--section must identify a section within the selected chapter")
        if not sections and section is not None:
            raise ValueError("The selected chapter has no sections; omit --section")
    if any(candidate.stem.lower() == local.lower() for candidate in path.parent.glob("*.lean")):
        raise FileExistsError(f"Node already exists (case-insensitive): {node_id}")
    retired = repo / "literature" / key / "retired.yaml"
    if retired.exists() and any(
        entry["id"] == node_id for entry in load_yaml(retired.read_text())["retired"]
    ):
        raise ValueError(f"Retired node ids cannot be reused: {node_id}")
    known_tags = {
        item["id"] for item in load_yaml((repo / "taxonomy/tags.yaml").read_text())["tags"]
    }
    if not tags or set(tags) - known_tags:
        raise ValueError(
            f"Supply at least one known tag; unknown: {sorted(set(tags) - known_tags)}"
        )
    auxiliary = local.startswith(("Aux_", "Bridge_"))
    cited = local.startswith("Cited_")
    if auxiliary != bool(parent and aux_kind and reason):
        raise ValueError("Aux_/Bridge_ nodes require exactly --parent, --aux-kind and --reason")
    if not auxiliary and any((parent, aux_kind, reason)):
        raise ValueError("Auxiliary options are valid only for Aux_/Bridge_ nodes")
    if auxiliary:
        parent_path = node_path(repo, parent or "")
        if parent_path.parent != path.parent or not parent_path.exists():
            raise ValueError("The auxiliary parent must exist in the same document")
        if (aux_kind == "bridge") != local.startswith("Bridge_"):
            raise ValueError(
                "Bridge_ nodes require aux-kind bridge; other auxiliaries cannot be bridges"
            )
    if cited != bool(cited_kind and used_at):
        raise ValueError("Cited_ nodes require --cited-kind and --used-at")
    if not cited and any((cited_kind, cited_ref, cited_doc, cited_locator, used_at)):
        raise ValueError("Citation options are valid only for Cited_ nodes")
    labels = {
        parse_header(candidate.read_text()).metadata["source"]["label"]
        for candidate in path.parent.glob("*.lean")
    }
    if cited:
        pages = pages or used_at
        if not label:
            base = f"Cited result (p. {(used_at or [0])[0]}"
            label = base + ")"
            number = 2
            while label in labels:
                label = f"{base}, {number})"
                number += 1
    if not label or not pages:
        raise ValueError("--label and --pages are required")
    if label in labels and not auxiliary:
        raise ValueError(f"Source label must be unique within {key}: {label}")
    metadata: dict[str, Any] = {
        "id": node_id,
        "doc": key,
        "kind": kind,
        "source": {"label": label, "pages": pages},
        "tags": list(dict.fromkeys(tags)),
        "concepts": {"defines": [], "uses": []},
        "deps": {"statement": [], "proof": []},
        "decls": [],
        "fidelity": {"status": "faithful"},
    }
    for field, value in (("chapter", chapter), ("section", section)):
        if value is not None:
            metadata["source"][field] = value
    if title:
        metadata["title"] = title
    if auxiliary:
        metadata["aux"] = {"parent": parent, "kind": aux_kind, "reason": reason}
    if cited:
        source = {"kind": cited_kind}
        for field, value in (("ref", cited_ref), ("doc", cited_doc), ("locator", cited_locator)):
            if value:
                source[field] = value
        metadata["cited"] = {"source": source, "used_at": used_at, "formulation": "verbatim"}
    errors = SchemaStore(repo / "schema").validate(metadata, "node-header.strict.schema.json")
    if errors:
        raise ValueError(errors[0].message)
    yaml = dump_metadata(metadata).rstrip()
    if "/-" in yaml or "-/" in yaml:
        raise ValueError("Comment delimiters are forbidden in a node header")
    text = (
        f"/-!\n```yaml node\n{yaml}\n```\n\n## Statement\n\nTODO: transcribe from p. {pages[0]}\n"
    )
    if kind in THEOREM_KINDS:
        text += f"\n## Proof\n\nTODO: transcribe the document's proof from p. {pages[0]}\n"
    text += "\n## Description\n\nTODO: describe the source item.\n-/\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)
    return path


def new_document_files(
    repo: Path, key: str, pdf: Path, *, title: str | None = None, authors: list[str] | None = None
) -> dict[str, str]:
    """Prepare registration metadata without copying the PDF into the public checkout."""
    if not DOC_KEY.fullmatch(key):
        raise ValueError(f"Invalid document key: {key}")
    if any(
        path.name.lower() == key.lower()
        for path in (repo / "literature").iterdir()
        if path.is_dir()
    ):
        raise ValueError(f"Document already registered (case-insensitive): {key}")
    try:
        import pymupdf
    except ImportError as exc:
        raise ValueError(
            "PDF registration requires: uv sync --project tools --extra ingest"
        ) from exc
    with pymupdf.open(pdf) as source:
        pages = len(source)
        pdf_metadata = source.metadata
    year = int(re.search(r"[0-9]{4}", key).group())
    metadata = {
        "schema_version": 1,
        "doc_key": key,
        "type": "article",
        "year": year,
        "title": title or pdf_metadata.get("title") or "TODO: verify source title",
        "authors": [{"family": author} for author in (authors or ["TODO: verify author"])],
        "language": "en",
        "foundations": [],
        "structure": [],
        "pdf": {
            "file": pdf.name,
            "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "pages": pages,
            "page_offset": 0,
            "license": {"id": "proprietary"},
            "sources": [],
        },
        "notes": (
            "Registration scaffold: verify bibliography, license, language "
            "and page offset before approval."
        ),
    }
    claim = {"schema_version": 1, "doc_key": key, "claims": []}
    schemas = SchemaStore(repo / "schema")
    for value, name in ((metadata, "document"), (claim, "claim")):
        errors = schemas.validate(value, f"{name}.schema.json")
        if errors:
            raise ValueError(f"{name}: {errors[0].message}")
    return {
        f"literature/{key}/document.yaml": dump_metadata(metadata),
        f"literature/{key}/claim.yaml": dump_metadata(claim),
    }
