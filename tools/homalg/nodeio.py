"""Read and rewrite authored node headers without changing surrounding Lean code."""

from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata, parse_metadata
from homalg.headers import Header, parse_header
from homalg.schemas import SchemaStore


def node_path(repo: Path, node_id: str) -> Path:
    """Validate a public node identity before using it in filesystem paths."""
    schemas = SchemaStore(repo / "schema")
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(
        schemas.schemas["common.schema.json"]["$defs"]["NodeId"], registry=schemas.registry
    )
    # NodeId is a standalone regular expression in the common schema.
    errors = list(validator.iter_errors(node_id))
    if errors:
        raise ValueError(f"Invalid node id: {node_id}")
    doc, local = node_id.split(".", 1)
    return repo / "HomAlg" / doc / f"{local}.lean"


def header_mapping(text: str, header: Header | None = None) -> dict[str, Any]:
    """Read a round-trip header mapping with its comments retained."""
    header = header or parse_header(text)
    body = text[header.start + 3 : header.end - 2]
    yaml = body.split("```yaml node", 1)[1].split("```", 1)[0]
    return parse_metadata(yaml)


def replace_header(text: str, metadata: dict[str, Any], schemas: SchemaStore) -> str:
    """Validate and serialize a header, retaining its prose and all Lean declarations."""
    errors = schemas.validate(metadata, "node-header.strict.schema.json")
    if errors:
        raise ValueError(f"Invalid replacement node header: {errors[0].message}")
    encoded = dump_metadata(metadata).rstrip()
    if "/-" in encoded or "-/" in encoded:
        raise ValueError("Comment delimiters are forbidden inside node headers")
    header = parse_header(text)
    body = text[header.start + 3 : header.end - 2]
    opening = body.index("```yaml node") + len("```yaml node")
    closing = body.index("```", opening)
    updated = body[:opening] + "\n" + encoded + "\n" + body[closing:]
    return text[: header.start + 3] + updated + text[header.end - 2 :]
