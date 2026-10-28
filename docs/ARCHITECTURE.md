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

## Checks and interfaces

Each implemented semantic check is a module exposing `check(ctx) -> list[Finding]`
and registered in `tools/homalg/checks/__init__.py`. File loading and syntax
diagnostics precede semantic checks. Invalid types are reported by schemas and
are not trusted by dependent rules. Unavailable context is explicitly listed.

All CLI commands accept `--repo`, `--json` and `--strict`. Exit codes are 0 for
success, 1 for failed findings, 2 for usage/configuration errors and 3 for failed
external tools. Full validation serializes Lake through the Horizon workspace
check lock. Infrastructure bootstrap runs without an active Horizon session.
