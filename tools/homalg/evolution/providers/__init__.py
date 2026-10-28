"""Providers implement complete(prompt, schema, model, max_tokens), DEFAULT_MODEL and PRICES."""

import importlib
import re
from importlib.metadata import entry_points
from typing import Any


def load_provider(name: str) -> Any:
    """Load a bundled adapter or an explicitly installed provider entry point."""
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
        raise ValueError("Invalid provider name")
    plugins = entry_points(group="homalg.evolution.providers", name=name)
    if plugins:
        return next(iter(plugins)).load()
    try:
        return importlib.import_module(f"homalg.evolution.providers.{name.replace('-', '_')}")
    except ModuleNotFoundError as exc:
        raise ValueError(
            f"Provider {name!r} is not installed; install its homalg evolution plugin"
        ) from exc
