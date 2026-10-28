"""Dispute histories, private source provenance and prerender diagnostics."""

import hashlib
import re
from pathlib import Path
from typing import Any

from homalg.checks.context import Context, Finding
from homalg.checks.text_rules import finding
from homalg.headers import HeaderError, parse_header
from homalg.schemas import load_yaml

MARKERS = {"statement": "STATEMENT-DISPUTED:", "proof": "PROOF-DISPUTED:"}


def dispute_sync(ctx: Context) -> list[Finding]:
    """Header disputes and primary docstring markers must describe the same active problem."""
    result = []
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        names = metadata.get("decls", [])
        if not names:
            continue
        primary = {
            command.name: command for command in ctx.commands.get(path, []) if command.name in names
        }
        dispute = metadata.get("dispute", {})
        if dispute.get("status") == "open":
            command = primary.get(names[0])
            expected = MARKERS[dispute["kind"]]
            if command is None or expected not in command.docstring:
                result.append(
                    finding("dispute-sync", path, f"Primary docstring must contain {expected}")
                )
            wrong = MARKERS["proof" if dispute["kind"] == "statement" else "statement"]
            if any(wrong in command.docstring for command in primary.values()):
                result.append(
                    finding(
                        "dispute-sync",
                        path,
                        "Docstring contains a marker for the wrong dispute kind",
                    )
                )
        elif any(
            marker in command.docstring
            for command in primary.values()
            for marker in MARKERS.values()
        ):
            result.append(
                finding(
                    "dispute-sync",
                    path,
                    "A resolved/absent dispute must not leave an active docstring marker",
                )
            )
    return result


def dispute_valid(ctx: Context) -> list[Finding]:
    """Resolution routes preserve source errors and append-only dispute history."""
    result = []
    by_node = ctx.node_headers()
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        deviations = {item["kind"] for item in metadata["fidelity"].get("deviations", [])}
        records = [*metadata.get("dispute_history", [])]
        if "dispute" in metadata:
            records.append(metadata["dispute"])
        for record in records:
            if record["status"] != "resolved":
                continue
            via = record["resolution"]["via"]
            error = None
            if via == "withdrawn" and record.get("confirmed_by"):
                error = "A confirmed dispute cannot be withdrawn"
            elif via == "erratum" and (
                "erratum" not in deviations
                or (
                    record["kind"] == "statement"
                    and not header.sections.get("Statement (corrected)")
                )
            ):
                error = (
                    "An erratum resolution requires the erratum deviation "
                    "and a corrected statement for statement errors"
                )
            elif via == "proof-route" and (
                record["kind"] != "proof" or "proof-route" not in deviations
            ):
                error = (
                    "A proof-route resolution requires a proof dispute "
                    "and an explicit proof-route deviation"
                )
            if error:
                result.append(finding("dispute-valid", path, error))
    if ctx.pr:
        for path, before in ctx.base_sources.items():
            if not re.fullmatch(r"HomAlg/[^/]+/[^/]+\.lean", path):
                continue
            try:
                old = parse_header(before).metadata
            except HeaderError:
                continue
            new = ctx.all_headers[path].metadata if path in ctx.all_headers else {}
            history = old.get("dispute_history", [])
            if new.get("dispute_history", [])[: len(history)] != history:
                result.append(finding("dispute-valid", path, "Dispute history is append-only"))
            if "dispute" in old:
                candidates = [new.get("dispute", {}), *new.get("dispute_history", [])]
                original = old["dispute"]
                # Guarded resolution changes status/confirmation/resolution but retains
                # the original identity and report. An exact comparison would reject
                # the specified open -> resolved transition itself.
                immutable = set(original) - {
                    "status",
                    "resolution",
                    "confirmed_by",
                    "confirmed_on",
                    "issue",
                }
                retained = any(
                    all(candidate.get(key) == original[key] for key in immutable)
                    and all(
                        candidate.get(key) == original[key]
                        for key in ("confirmed_by", "confirmed_on")
                        if key in original
                    )
                    for candidate in candidates
                )
                if not retained:
                    result.append(
                        finding(
                            "dispute-valid",
                            path,
                            "The original dispute report must remain current or in history",
                        )
                    )
    for key in ctx.docs:
        for path in sorted((ctx.repo / "literature" / key / "run-log/inbox").glob("*.yaml")):
            try:
                entry = load_yaml(path.read_text())
                if not isinstance(entry, dict) or entry.get("kind") != "dispute":
                    continue
                nodes = entry.get("scope", {}).get("blueprint_nodes", [])
                if entry.get("node"):
                    nodes = [*nodes, entry["node"]]
                for node in nodes:
                    node = node.removeprefix("label:")
                    header = by_node.get(node)
                    if header is None or not (
                        header.metadata.get("dispute") or header.metadata.get("dispute_history")
                    ):
                        result.append(
                            finding(
                                "dispute-valid",
                                path.relative_to(ctx.repo).as_posix(),
                                f"Archived dispute has no retained node dispute: {node}",
                            )
                        )
            except (ValueError, TypeError, AttributeError) as error:
                result.append(
                    finding("dispute-valid", path.relative_to(ctx.repo).as_posix(), str(error))
                )
    return result


def normalized_excerpt(text: str) -> str:
    """Apply only the markup/editorial normalization specified for provenance checks."""
    # Math is byte-sensitive: subscripts, intervals and bracket expressions must
    # survive markup normalization. Apply prose normalization around math spans.
    parts = re.split(r"(\$\$[\s\S]*?\$\$|(?<!\\)\$[^$]*?(?<!\\)\$)", text)
    for index in range(0, len(parts), 2):
        prose = parts[index]
        prose = re.sub(r"\[[^]\n]*\]", "", prose)
        prose = re.sub(
            r"\\(?:begin|end)\{(?:theorem|lemma|proof|definition|proposition|remark|corollary)\}",
            "",
            prose,
        )
        prose = re.sub(r"\\(?:textbf|textit|emph)\{([^{}]*)\}", r"\1", prose)
        prose = re.sub(r"(?<!\w)(\*\*|__|\*|_)(.+?)\1(?!\w)", r"\2", prose)
        parts[index] = prose.replace("`", "")
    return " ".join("".join(parts).split())


def join_reviewed_pages(pages: list[str]) -> str:
    """Join body paragraphs across pages while retaining separately searchable footnotes."""
    bodies, footnotes = [], []
    for page in pages:
        page = re.sub(r"(?m)^%[^\n]*(?:\n|$)", "", page)
        parts = re.split(r"(?=\\paragraph\{\[Footnote \d+\]\})", page, maxsplit=1)
        bodies.append(parts[0])
        if len(parts) == 2:
            footnotes.append(parts[1])
    return "\n".join(bodies + footnotes)


def statement_provenance(ctx: Context) -> list[Finding]:
    """Compare paragraphs against the exact reviewed private page versions."""
    result = []
    cache: dict[str, dict[str, Any]] = {}
    for path, header in ctx.valid_headers.items():
        metadata = header.metadata
        key = metadata["doc"]
        if (
            key.startswith("Fixture")
            or "aux" in metadata
            or metadata.get("cited", {}).get("formulation") == "editorial"
        ):
            continue
        private = ctx.repo / "literature/.private" / key
        manifest = private / "transcription.yaml"
        if not manifest.exists():
            continue
        if key not in cache:
            try:
                record = load_yaml(manifest.read_text())
                errors = ctx.schemas.validate(record, "transcription.schema.json")
                if errors:
                    raise ValueError(errors[0].message)
                cache[key] = record
            except (OSError, ValueError) as error:
                result.append(
                    finding(
                        "statement-provenance",
                        path,
                        f"Invalid private transcription manifest: {error}",
                        severity="warning",
                    )
                )
                cache[key] = {}
        record = cache[key]
        if not record:
            continue
        doc = ctx.all_docs[key]
        if record.get("pdf_sha256") != doc.get("pdf", {}).get("sha256"):
            result.append(
                finding(
                    "statement-provenance",
                    path,
                    "Private transcription belongs to a different PDF version",
                    severity="warning",
                )
            )
            continue
        pages = []
        for printed in metadata["source"]["pages"]:
            index = printed + doc.get("pdf", {}).get("page_offset", 0)
            number = f"{index:04d}"
            page = private / "tex" / f"page-{number}.tex"
            item = record["pages"].get(number, {})
            if not page.is_file():
                result.append(
                    finding(
                        "statement-provenance",
                        path,
                        f"Private page {number} is missing",
                        severity="warning",
                    )
                )
                continue
            content = page.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            reviews = item.get("reviews", [])
            if (
                item.get("status") != "reviewed"
                or item.get("file_sha256") != digest
                or not reviews
                or reviews[-1].get("status") != "satisfactory"
                or reviews[-1].get("file_sha256") != digest
            ):
                result.append(
                    finding(
                        "statement-provenance",
                        path,
                        f"Private page {number} has no satisfactory review of its current bytes",
                        severity="warning",
                    )
                )
                continue
            pages.append(content.decode())
        source = normalized_excerpt(join_reviewed_pages(pages))
        titles = ["Statement" if doc.get("language", "en") == "en" else "Statement (original)"]
        if metadata.get("nl_proof_source", {}).get("follows", "document") == "document":
            titles.append("Proof")
        for title in titles:
            for paragraph in re.split(r"\n\s*\n", header.sections.get(title, "")):
                normalized = normalized_excerpt(paragraph)
                if normalized and normalized not in source:
                    result.append(
                        finding(
                            "statement-provenance",
                            path,
                            f"{title} paragraph is not present in reviewed pages: "
                            f"{paragraph.splitlines()[0][:100]}",
                            severity="warning",
                            line=header.section_lines.get(title),
                        )
                    )
    return result


def markdown_renders(ctx: Context) -> list[Finding]:
    """Surface prerenderer KaTeX errors and broken node links for the selected documents."""
    result = []
    keys = set(ctx.docs)
    if ctx.pr and ctx.changed_paths:
        keys = {
            Path(path).parts[1]
            for path in ctx.changed_paths
            if len(Path(path).parts) > 2 and Path(path).parts[0] in {"HomAlg", "literature"}
        }
    for entry in ctx.health.get("markdown_findings", []):
        node = entry.get("node", "")
        doc = entry.get("doc") or node.split(".")[0]
        if doc in keys:
            result.append(
                finding(
                    "markdown-renders",
                    "site/public/data/health.json",
                    f"{node}: {entry.get('message', entry.get('error', entry))}",
                    severity="warning",
                )
            )
    return result
