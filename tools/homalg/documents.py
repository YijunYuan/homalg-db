"""Comment-preserving metadata I/O with schema validation and atomic replacement."""

from copy import deepcopy
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from homalg.io import atomic_write
from homalg.repository import DOC_KEY
from homalg.schemas import SchemaStore, load_yaml


def parse_metadata(text: str) -> CommentedMap:
    """Reject ambiguous YAML, then retain comments, ordering and quoted scalars."""
    value = load_yaml(text)
    if not isinstance(value, dict):
        raise ValueError("Metadata must be a YAML mapping")
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = False
    return yaml.load(text)


def dump_metadata(value: dict[str, Any]) -> str:
    """Serialize metadata without losing comments; quote newly assigned strings."""

    def quote(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if type(child) is str:
                    item[key] = DoubleQuotedScalarString(child)
                else:
                    quote(child)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                if type(child) is str:
                    item[index] = DoubleQuotedScalarString(child)
                else:
                    quote(child)

    value = deepcopy(value)
    quote(value)
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 100
    yaml.representer.ignore_aliases = lambda data: True
    yaml.indent(mapping=2, sequence=4, offset=2)
    stream = StringIO()
    yaml.dump(value, stream)
    return stream.getvalue()


def read_metadata(path: Path, schema: str, schemas: SchemaStore) -> CommentedMap:
    """Read and validate a metadata document before exposing it to callers."""
    value = parse_metadata(path.read_text(encoding="utf-8"))
    errors = schemas.validate(value, schema)
    if errors:
        raise ValueError(f"{path}: {errors[0].message}")
    return value


def write_metadata(path: Path, value: dict[str, Any], schema: str, schemas: SchemaStore) -> None:
    """Validate before writing, so failures never damage the original metadata."""
    errors = schemas.validate(value, schema)
    if errors:
        raise ValueError(f"{path}: {errors[0].message}")
    atomic_write(path, dump_metadata(value))


def read_document(repo: Path, key: str, schemas: SchemaStore | None = None) -> CommentedMap:
    """Read one registered document and enforce its identity/year invariants."""
    if not DOC_KEY.fullmatch(key):
        raise ValueError(f"Invalid document key: {key}")
    schemas = schemas or SchemaStore(repo / "schema")
    value = read_metadata(
        repo / "literature" / key / "document.yaml", "document.schema.json", schemas
    )
    import re

    year = re.search(r"[0-9]{4}", key)
    if value["doc_key"] != key or not year or value["year"] != int(year.group()):
        raise ValueError("Document identity/year must match its containing directory")
    return value
