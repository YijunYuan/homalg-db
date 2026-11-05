# Architecture

HomAlgDB separates formalization, metadata processing, presentation and local
agent orchestration. Components exchange versioned file contracts rather than
depending on each other's internals. This is the bootstrap English summary of
sections 3 and 4 of the approved requirements, version 1.0 (2026-10-27).

## Sources of truth

| Data | Authored or authoritative source | Generated output |
| --- | --- | --- |
| Node metadata and original prose | First module comment in each Lean node | `nodes.json.authored` |
| Bibliography and foundation boundary | `literature/<DocKey>/document.yaml` | Document records |
| Claim ownership | `literature/<DocKey>/claim.yaml` | Claim status and summaries |
| Local declaration information | Compiled Lean environment | `nodes.json.derived` |
| Global closure, axioms and status | Joined export and document inputs | `build/index.json` |
| Vocabulary and conceptual relations | `taxonomy/**/*.yaml` | Site taxonomy and evolution data |
| Draft ownership and review handoff | Explicit scope, actual identities and frozen input fingerprints | Isolated candidate work and check evidence; no approval implied |

Committed generated files depend only on their document and pinned toolchain.
They do not contain timestamps, commits or global dependency closure. The global
index and content-addressed site bundles are disposable build outputs.

## Repository boundaries

- `HomAlg/<DocKey>/<LocalId>.lean`: one flat directory per document; one node per
  file. The node id is `<DocKey>.<LocalId>` and its module is `HomAlg.<id>`.
- `HomAlg.lean` and `HomAlg/<DocKey>.lean`: generated roots. Document roots import
  source items and bridges. Auxiliary and cited nodes are reached through users.
- `HomAlgExport/Main.lean`: the standalone Lean export process.
- `tools/homalg/`: pure parsing/generation functions, command-line I/O and checks.
- `schema/`: draft 2020-12 contracts; all references resolve locally and validation
  enables format assertions, including dates and URIs.
- `literature/`: public metadata. Its ignored `.private/` checkout will hold PDFs
  and reviewed page transcriptions; public records do not redistribute them.
- `site/`: the static React application, with generated TypeScript contracts,
  worker-based layout/search and interchangeable static/API data adapters.
- `docs/fixtures/`: original, paginated synthetic source documents for tests.
- `horizon/`: local engine configuration and stage templates. The separate
  `homalg-horizon` fork supplies the scheduler, private ledger and dashboard.

## Pipeline

The pipeline is `gen-roots` → `extract` → `export-lean` (including the shared-lock
Lean build) → `index` → `site-data` → site build. `extract` preserves existing
derived records. The exporter supplies compiled facts; the index computes global
closure and statuses. Content-addressed site artifacts and SQLite project the
same versioned contracts.

Generated JSON uses sorted keys, two-space indentation, UTF-8 and a final newline.
Writes use a sibling temporary file and atomic replacement. Unchanged output
does not rewrite the destination. Node JSON and root freshness are reproducible
without volatile build metadata.

## Parallel preparation and acceptance

See [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md) for the coordination contract.
Draft authors use isolated source checkouts with disjoint ownership and fixed
dependency inputs. Review consumes a frozen handoff; canonical integration
rechecks those inputs rather than trusting a worker's success flag. Source
snapshots identify input bytes and are separate from compiled exports and review
approval. Each node retains its own independent review and compiled hashes when
several nodes share a compilation/export operation.

The private ledger, task evaluator and session hooks remain distinct from the
user's Git history. A local worker check or promotion is not a completed stage,
private-source validation or permission to publish. Shared canonical writes and
their finalization are coordinated through guarded boundaries.

## Checks and interfaces

Each implemented semantic check is a module exposing `check(ctx) -> list[Finding]`
and registered in `tools/homalg/checks/__init__.py`. File loading and syntax
diagnostics precede semantic checks. Invalid types are reported by schemas and
are not trusted by dependent rules. Unavailable context is explicitly listed.

All CLI commands accept `--repo`, `--json` and `--strict`. Exit codes are 0 for
success, 1 for failed findings, 2 for usage/configuration errors and 3 for failed
external tools. Full validation serializes Lake through the Horizon workspace
check lock. Infrastructure bootstrap runs without an active Horizon session.

Input reuse is local to a check or planning call. A validation context pins each
document's already-fetched status history to one immutable Git object id; each
node's claim, time and scope decision remains separate. A planning call indexes
authored nodes and inventory order once while retaining the exact node lists and
scopes for every task kind. New contexts and planning calls reread their inputs.
Neither mechanism caches approval, compiled evidence or stage completion, and
neither removes validation or export freshness checks. Measured acceptance and
limitations are recorded in [IMPLEMENTATION.md](IMPLEMENTATION.md).
