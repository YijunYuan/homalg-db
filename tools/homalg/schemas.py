"""Offline draft 2020-12 schemas and the project's restricted YAML 1.2 reader."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from ruamel.yaml import YAML
from ruamel.yaml.tokens import AliasToken, AnchorToken, KeyToken, ScalarToken, TagToken


class YamlError(ValueError):
    """A YAML error with a one-based source line."""

    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.line = line


def load_yaml(text: str) -> Any:
    """Read safe YAML without anchors, aliases, custom tags, merges or duplicates."""
    yaml = YAML(typ="safe", pure=True)
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    try:
        previous = None
        for token in yaml.scan(text):
            if isinstance(token, (AnchorToken, AliasToken, TagToken)):
                raise YamlError(
                    "YAML anchors, aliases and explicit tags are forbidden",
                    token.start_mark.line + 1,
                )
            if isinstance(previous, KeyToken) and isinstance(token, ScalarToken):
                if token.value == "<<":
                    raise YamlError("YAML merge keys are forbidden", token.start_mark.line + 1)
            previous = token
        result = yaml.load(text)
    except YamlError:
        raise
    except Exception as exc:
        mark = getattr(exc, "problem_mark", None)
        raise YamlError(str(exc), mark.line + 1 if mark else 1) from exc

    def check_merges(value: Any) -> None:
        if isinstance(value, dict):
            if "<<" in value:
                raise YamlError("YAML merge keys are forbidden")
            for child in value.values():
                check_merges(child)
        elif isinstance(value, list):
            for child in value:
                check_merges(child)

    check_merges(result)
    return result


class SchemaStore:
    """Resolve only local, explicitly registered schemas; never fetch the network."""

    def __init__(self, directory: Path):
        self.schemas = {
            str(path.relative_to(directory)): json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(directory.rglob("*.schema.json"))
        }
        self.registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in self.schemas.values()
        )

    def check_schemas(self) -> None:
        """Raise SchemaError if any schema violates the meta-schema."""
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)

    def validate(self, data: Any, schema_name: str) -> list[ValidationError]:
        """Return deterministic validation errors, with format assertions enabled."""
        validator = Draft202012Validator(
            self.schemas[schema_name],
            registry=self.registry,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )
        return sorted(validator.iter_errors(data), key=lambda err: str(list(err.absolute_path)))
