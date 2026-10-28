"""Explicit local provider execution with conservative cumulative spending reservations."""

import copy
import json
import math
import os
import tomllib
from decimal import Decimal
from pathlib import Path
from typing import Any

from homalg.evolution.bundle import build_bundle, canonical_json
from homalg.evolution.importer import EvolutionError, import_output
from homalg.evolution.providers import load_provider


def personal_config(path: Path | None = None) -> dict[str, Any]:
    path = (
        path
        or Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "homalg/evolution.toml"
    )
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def output_schema(repo: Path) -> dict[str, Any]:
    """Expand local common references; providers must not fetch schema URLs."""
    schema = json.loads((repo / "schema/evolution-output.schema.json").read_text())
    common = json.loads((repo / "schema/common.schema.json").read_text())["$defs"]

    def expand(value: Any) -> Any:
        if isinstance(value, dict):
            if "$ref" in value:
                name = value["$ref"].split("/")[-1]
                if name not in common:
                    raise EvolutionError(f"Unsupported schema reference: {value['$ref']}")
                return expand(copy.deepcopy(common[name]))
            return {key: expand(child) for key, child in value.items()}
        if isinstance(value, list):
            return [expand(child) for child in value]
        return value

    return expand(schema)


def positive_decimal(value: Any, name: str, *, allow_zero: bool = False) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise EvolutionError(f"{name} must be a finite positive number") from exc
    if not result.is_finite() or result < 0 or (result == 0 and not allow_zero):
        raise EvolutionError(f"{name} must be a finite positive number")
    return result


def input_upper_bound(prompt: str, schema: dict[str, Any]) -> int:
    """UTF-8 byte-token worst case plus schema and 8,192 framing tokens; no chars/4 guess."""
    return len(prompt.encode("utf-8")) + len(canonical_json(schema).encode("utf-8")) * 2 + 8192


def run(
    repo: Path,
    index: dict[str, Any],
    concepts: list[str],
    *,
    max_cost: Any,
    provider_name: str | None = None,
    model: str | None = None,
    max_tokens: int = 8192,
    price_in: Any = None,
    price_out: Any = None,
    by: str | None = None,
    config_path: Path | None = None,
    provider: Any = None,
) -> dict[str, Any]:
    """Reserve each request's upper bound against the entire run before any model call."""
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise EvolutionError("Model execution is local only and is disabled in CI")
    cap = positive_decimal(max_cost, "max-cost")
    config = personal_config(config_path)
    name = provider_name or config.get("provider", "openai")
    adapter = provider or load_provider(name)
    chosen_model = model or config.get("model") or adapter.DEFAULT_MODEL
    prices = getattr(adapter, "PRICES", {}).get(chosen_model)
    if (price_in is None) != (price_out is None):
        raise EvolutionError("Provide both --price-in and --price-out (USD per million tokens)")
    if price_in is not None:
        prices = (price_in, price_out)
        budget_prices = prices
    else:
        budget_prices = getattr(adapter, "BUDGET_PRICES", {}).get(chosen_model, prices)
    if prices is None or budget_prices is None:
        raise EvolutionError(
            f"Unknown prices for {chosen_model}; provide --price-in and --price-out"
        )
    rate_in, rate_out = [positive_decimal(value, "price", allow_zero=True) for value in prices]
    reserve_in, reserve_out = [
        positive_decimal(value, "budget price", allow_zero=True) for value in budget_prices
    ]
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 16:
        raise EvolutionError("max-tokens must be an integer of at least 16")
    if max_tokens > getattr(adapter, "MAX_OUTPUT_TOKENS", max_tokens):
        raise EvolutionError("max-tokens exceeds this provider's model limit")
    schema = output_schema(repo)
    reserved = Decimal(0)
    estimated_spent = Decimal(0)
    outputs = []
    stopped = None
    for concept in concepts:
        bundle = build_bundle(index, concept, repo=repo)
        if not bundle["nodes"]:
            raise EvolutionError(f"No concept-linked nodes to summarize: {concept}")
        upper_input = input_upper_bound(bundle["prompt"], schema)
        if upper_input + max_tokens > getattr(adapter, "MAX_CONTEXT_TOKENS", math.inf):
            raise EvolutionError("Conservative request size exceeds the model context limit")
        bound = (upper_input * reserve_in + max_tokens * reserve_out) / 1_000_000
        if reserved + bound > cap:
            stopped = {
                "concept": concept,
                "request_upper_bound_usd": float(bound),
                "remaining_usd": float(cap - reserved),
            }
            break
        reserved += bound
        # No retries: a failed or ambiguous request may already have incurred a charge.
        text, usage = adapter.complete(bundle["prompt"], schema, chosen_model, max_tokens)
        if set(usage) != {"input_tokens", "output_tokens"} or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in usage.values()
        ):
            raise EvolutionError("Provider returned invalid token usage; import refused")
        if usage["input_tokens"] > upper_input or usage["output_tokens"] > max_tokens:
            raise EvolutionError("Provider exceeded its reserved token bound; import refused")
        actual_bound = (
            usage["input_tokens"] * reserve_in + usage["output_tokens"] * reserve_out
        ) / 1_000_000
        # Report a conservative usage-based cost; retain the full reservation for later calls.
        # This covers long context/cache writes and never assumes discount eligibility.
        estimated_spent += actual_bound
        result = import_output(
            repo,
            json.loads(text),
            bundle,
            model=chosen_model,
            by=by,
            provider=name,
            usage=usage,
            cost=float(actual_bound),
            max_cost=float(cap),
        )
        outputs.append(
            {
                **result,
                "usage": usage,
                "cost_upper_bound_usd": float(actual_bound),
                "request_upper_bound_usd": float(bound),
            }
        )
    return {
        "provider": name,
        "model": chosen_model,
        "max_cost_usd": float(cap),
        "reserved_usd": float(reserved),
        "cost_upper_bound_usd": float(estimated_spent),
        "results": outputs,
        "budget_stopped": stopped,
        "price_in": float(rate_in),
        "price_out": float(rate_out),
    }
