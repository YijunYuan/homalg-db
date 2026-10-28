"""OpenAI Responses adapter; official model/pricing snapshot verified 2026-10-28.

Sources: https://developers.openai.com/api/docs/models/gpt-6.1-sol
https://developers.openai.com/api/docs/pricing
https://developers.openai.com/api/docs/guides/reasoning
https://developers.openai.com/api/docs/guides/structured-outputs
"""

import copy
import json
import os
from typing import Any

DEFAULT_MODEL = "gpt-6.1-sol"
# USD per million tokens, standard short-context input/output prices.
PRICES = {
    "gpt-6.1-sol": (2, 10),
    "gpt-6.1-terra": (1, 5),
    "gpt-6-astra": (10, 50),
    "gpt-6-luna": (0.1, 0.5),
}
# Reserve long-context + maximum cache-write pricing, without assuming a cache hit.
# The same ceiling rates produce the usage-based upper bound stored as cost_usd.
BUDGET_PRICES = {
    model: (price_in * 5, price_out * 1.5) for model, (price_in, price_out) in PRICES.items()
}
MAX_OUTPUT_TOKENS = 128000
MAX_CONTEXT_TOKENS = 1050000


def strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Make optional output members nullable for the Responses strict-schema subset."""
    value = copy.deepcopy(schema)

    def convert(item: Any) -> None:
        if isinstance(item, dict):
            for child in item.values():
                convert(child)
            item.pop("$id", None)
            item.pop("$schema", None)
            if item.get("type") == "object":
                required = set(item.get("required", []))
                for key, prop in item.get("properties", {}).items():
                    if key not in required:
                        item["properties"][key] = {"anyOf": [prop, {"type": "null"}]}
                item["required"] = list(item.get("properties", {}))
                item["additionalProperties"] = False
        elif isinstance(item, list):
            for child in item:
                convert(child)

    convert(value)
    return value


def complete(
    prompt: str, schema: dict[str, Any], model: str, max_tokens: int
) -> tuple[str, dict[str, int]]:
    """One bounded request, with no automatic retries or external tools."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required for the local OpenAI provider")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError(
            "Install the evolution extra: uv sync --project tools --extra evolution"
        ) from exc
    client = OpenAI(base_url="https://api.openai.com/v1", max_retries=0, timeout=120)
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_tokens,
            reasoning={"effort": "medium"},
            service_tier="default",
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "concept_evolution",
                    "strict": True,
                    "schema": strict_schema(schema),
                }
            },
        )
    except Exception as exc:
        raise RuntimeError("OpenAI request failed; no retry was attempted") from exc
    if response.status != "completed" or not response.output_text:
        raise RuntimeError(
            "OpenAI returned an incomplete response or refusal; no import was written"
        )
    if response.usage is None:
        raise RuntimeError("OpenAI omitted token usage; no import was written")

    def remove_nulls(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: remove_nulls(child) for key, child in value.items() if child is not None}
        if isinstance(value, list):
            return [remove_nulls(child) for child in value]
        return value

    text = json.dumps(remove_nulls(json.loads(response.output_text)), ensure_ascii=False)
    return text, {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
