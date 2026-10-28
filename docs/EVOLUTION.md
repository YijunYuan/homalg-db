# Concept evolution

The evolution layer keeps mathematical evidence, generated interpretations and review decisions separate. Concept links and effective relations are included in `homalg index`; the site presents document graphs, concept timelines, definition comparisons and a Sigma node graph. Unreviewed relations are hidden from these graphs until the reader enables them. Rejected relations never appear as graph edges. Versions connected by `previous_edition` share a document lane.

## Bundle and import without a model call

```sh
uv run --project tools homalg evolution bundle chain-complex --out build/evolution/chain-complex.bundle.json
uv run --project tools homalg evolution bundle --all --out build/evolution
uv run --project tools homalg evolution status --json
uv run --project tools homalg evolution import build/evolution/chain-complex.output.json \
  --bundle build/evolution/chain-complex.bundle.json --model external-model --by contributor
```

`bundle` and `status` build a fresh index by default; `--index build/index.json` deliberately uses an existing snapshot. The bundle contains the concept, documents sorted by year, natural-language statements, available Lean signatures, fidelity and Mathlib evidence, accepted relations, rejected relations as negative evidence, previous summaries, and a versioned prompt. Concept aliases resolve through `merged_into`. The prompt includes the original output schema verbatim and the referenced common definitions.

`bundle_sha256` hashes only canonical JSON for `concept`, `documents`, `nodes` and `relations`. Commit IDs, timestamps, prompts, previous summaries and the derived hash itself do not affect it. A changed hypothesis or effective relationship does. The index's concept projection adds `current_bundle_sha256`; authored concepts remain strict. Site evolution records derive each version's `stale` flag from this hash. The index does not add `stale` to the strict authored summary schema.

Import validates the output schema, the evidence hash, concept, all stage node IDs and document membership, relation endpoints, and node-ID citations in text. It never calls a model. Invalid input exits 1 before writing. Successful imports append a new version, preserve older versions and always start unreviewed. Canonical relation triples already present in any review state are skipped and reported. New relations go to `taxonomy/relations/llm-YYYY-MM-DD.yaml`. Files are validated before replacement; a failed multi-file write restores completed replacements. A repository-local lock serializes imports and reviews.

## Optional local provider execution

```sh
uv sync --project tools --extra evolution
# Supply OPENAI_API_KEY through your shell or secret manager.
uv run --project tools --extra evolution homalg evolution run chain-complex \
  --max-cost 2 --max-tokens 8192 --by contributor
uv run --project tools --extra evolution homalg evolution run --stale --max-cost 5
```

The provider and model order is command-line option, personal configuration, then provider default. The personal file is `$XDG_CONFIG_HOME/homalg/evolution.toml` or `~/.config/homalg/evolution.toml`:

```toml
provider = "openai"
model = "gpt-6.1-sol"
```

The OpenAI adapter uses Responses with a strict JSON schema, medium reasoning effort, the standard service tier, `store=false`, no external tools and no automatic retries. Nullable optional properties required by the provider's strict schema are removed before the repository schema is checked. A refusal, incomplete response or missing/invalid usage prevents import. A failed request may still incur a provider charge; the caller decides whether to retry.

`--max-cost` is mandatory and applies to the complete invocation, including `--stale`. Before each request, the runner reserves a conservative input-token bound (UTF-8 bytes, twice the schema bytes and 8,192 framing tokens) plus the maximum output budget. It retains the full reservation for later requests even if actual usage was lower. A request that would exceed the remaining budget is not sent; the CLI reports the stopped concept and exits 1. Unknown model prices require both `--price-in` and `--price-out`, in USD per million tokens. Explicit prices must cover the selected provider's applicable pricing tiers.

The bundled rates and default were verified against official documentation on **2026-10-28**. The default is `gpt-6.1-sol`, with a standard input/output base price of $2/$10 per million tokens. The adapter reserves five times the base input price and 1.5 times the base output price to cover the documented long-context and maximum cache-write multipliers. `provenance.cost_usd` therefore records a conservative usage-based upper bound, not an invoice amount. Token usage, maximum run cost, model, provider, prompt version and evidence commit/hash are retained. Pricing and model availability require maintenance when providers change them. See the [model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [pricing](https://developers.openai.com/api/docs/pricing), [reasoning](https://developers.openai.com/api/docs/guides/reasoning), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) and [token counting](https://developers.openai.com/api/docs/guides/token-counting).

Model execution is disabled when `CI` or `GITHUB_ACTIONS` is set. No model key belongs in repository files, CI secrets or scheduled workflows. Bundle/import/status/review remain usable offline.

## Provider plugins

A bundled module `homalg.evolution.providers.<name>` or installed entry point in the `homalg.evolution.providers` group exports:

```python
DEFAULT_MODEL = "provider-model"
PRICES = {"provider-model": (input_usd_per_million, output_usd_per_million)}

def complete(prompt, schema, model, max_tokens):
    return json_text, {"input_tokens": input_count, "output_tokens": output_count}
```

Providers may additionally expose `BUDGET_PRICES`, `MAX_OUTPUT_TOKENS` and `MAX_CONTEXT_TOKENS`. They must honor the output cap, report complete input/output usage including reasoning, avoid retries and chargeable tools, and use a tokenizer for which the runner's UTF-8-byte bound is conservative. A plugin that cannot satisfy those assumptions must implement and document a compatible bound before use. OpenAI is the built-in provider; other names require an installed module or entry point. Personal API keys stay in each provider's normal environment variables.

## Review and stale summaries

```sh
uv run --project tools homalg evolution review rel-12345678 --accept --by reviewer --note 'Checked against both statements.'
uv run --project tools homalg evolution review --summary chain-complex 1 --reject --by reviewer
uv run --project tools homalg evolution bundle --stale --out build/evolution
```

Relation reviews write only `taxonomy/relations/_reviews.yaml`, including header-origin relation IDs. Summary reviews update the selected version. These commands prepare protected changes for a CODEOWNERS-reviewed PR; they do not approve or merge a PR. Suggestions do not modify the concept registry automatically. The site shows version, review status, provenance, stale warning, stages, open questions and proposed aliases. Natural-language citations are subject to the same Markdown link checks as the rest of the site.

## Validation and remaining evidence

`tools/tests/test_evolution.py` covers semantic hashing, rejected/unreviewed relation handling, merged concepts, imports with invented references, transaction rollback, canonical deduplication, review registries, stale detection, unknown prices, cumulative cost limits, provider configuration, strict OpenAI request shape and token accounting. Provider calls are fakes; no paid request is needed for tests. Browser tests exercise default relation isolation, the unreviewed toggle, definition comparisons, summaries and document-edge details.

The synthetic Fixture2000/Fixture2001 data proves the pipeline contracts. A separate [real two-source rehearsal](evolution/README.md) uses the 1945 pilot and Hochschild's 1942 primary paper. The interactive session generated its source-grounded summary, then the actual importer stored version 1 unreviewed in an isolated build repository; site-output validation also passed. Exact model identity is recorded as not reported, and provider/usage/cost fields are omitted. The second source remains unregistered in the live database, so the exercise does not publish dangling node references. A paid provider smoke test and substantive human review remain separate from that completed offline rehearsal.

## Independent agent review

When the owner-enabled `horizon/review-policy.yaml` permits independent agent
reviews, an actual independent reviewer may add provenance with:

```sh
uv run --project tools homalg evolution review --summary chain-complex 1 --accept \
  --by review-agent --session reviewer-session --author-session author-session \
  --report docs/evolution/chain-complex-v1-review.md
```

The public report must identify the source evidence and contain exactly one of
each binding line. For a relation, `Subject` is its permanent `rel-...` id and the
bundle line is needed only when its provenance contains a bundle hash. For a
summary, `Subject` is `CONCEPT:VERSION`:

```text
Session: reviewer-session
Author-session: author-session
Subject: chain-complex:1
Subject-sha256: <homalg.evolution.reviews.subject_hash of the reviewed record>
Bundle-sha256: <the summary's provenance.bundle_sha256>
Verdict: satisfactory
Assertions-checked: yes
Source-evidence: <primary sources and precise locators actually checked>
```

The reviewer checks every assertion and proposed relationship against the cited
source and bundle; the report is not an automatic mathematical proof. A rejected
review uses `Verdict: unsatisfactory`. The command requires the tracked policy,
different nonempty sessions, a public report within the checkout, the exact
reviewed-content hash, and the exact bundle hash where present. It records
`kind: agent`, both sessions, report path/SHA-256 and subject SHA-256. Indexing
rejects a changed report or changed reviewed assertions until a new review is
written. The site identifies these as independent agent reviews. Existing
protected-PR review commands remain available, and no command grants CODEOWNERS
approval, merges a PR or modifies vocabulary acceptance.

Historical node moves are resolved in effective relation endpoints without
changing permanent relation IDs or the review registry keys. Alias projection
does not erase the original review identity. The index and site manifest retain
optional `retired` records, so historical node links display reasons and resolve
to current data. A pruned or missing replacement is shown as unavailable rather
than fabricated. Old tag/concept query filters resolve to their surviving ids.
