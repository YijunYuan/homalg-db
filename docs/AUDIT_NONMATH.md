# Non-mathematical requirements audit

Audit date: 2026-10-28. This is a local implementation audit against requirements
version 1.0 and the owner's later independent-review policy. Remote publication,
remote PR approval and external CI acceptance remain separate operations.

| Area | Finding and evidence |
| --- | --- |
| M0 contracts | Schema checks and generated TypeScript preserve strict contracts. New optional retirement and review fields are described below; empty retirement registries do not change fixture output. |
| M1 retirement | Fixed a real mismatch: validation resolved moved/merged ids while global relation loading did not. `retired.py` validates registries and rejects duplicate ids/cycles. `relations.py` resolves endpoints and duplicate/self edges while retaining authored relation IDs and review keys. The global index retains permanent tombstones and rejects reuse of live ids. |
| M2/M7 historical navigation | Static and SQLite/API node/dependency requests resolve the same move/merge chains. Old node pages display reason/date/author and link to the live node; pruning and absent replacements retain an explanation. Search facets resolve historical tag/concept ids. Tests cover chains, cycles, stale targets, canonical payload equality and real browser navigation. |
| M3 publication readiness | Existing governance tooling previews labels, rulesets, ownership and repository settings before applying them. `check_public_tree.py` inspects tracked and normally addable files without staging or publishing. It rejects private/runtime paths, PDFs and symlinks exposing private/external targets, including force-added ignored files. Main and fork both pass after removal of a generated Lighthouse browser profile. |
| M4 engine | Existing null-harness integration, fork session tests, private snapshot recovery and dashboard reference containment remain the concrete local evidence. A published wheel and cold-start remote PR are publication acceptance, not something local mocks can establish. The fork wheel is already built and public-tree preflight passes. |
| M6 review | Added explicit ordinary independent-agent evolution review under the tracked owner-enabled policy. Public source-checking reports, distinct sessions, subject/bundle hashes and report hashes are required; changed reports/assertions invalidate indexing. No human provenance is fabricated and GitHub owner approval remains unchanged. Vocabulary maintenance still uses its existing maintenance PR plus an actual independent report; it gains no automatic approval flag. |
| M7 API/security | Live API contract tests remain in `test_localdb.py`; immutable snapshot resources, exact identifier search, overview/chapter requests, truncation and CORS are exercised. Existing pinned-action/minimum-permission audit and dependency audit remain applicable. New publication-path checks cover a gap beyond the existing PDF-only rule. |
| Optional doc-gen4 | Remains disabled. The measurement plan below preserves all stated cost and publication gates. No build duration or artifact size is invented. |

## Contract decisions

The requirements demand historical moved/merged endpoint resolution and permanent
retirement explanations, but A.1 and the site-manifest table contain no retirement
projection. The minimal additive extension is optional `retired` in the global
index and manifest, using the existing `retired.schema.json` array unchanged.
Authored records stay in `literature/<DocKey>/retired.yaml`. The manifest's existing
200 KB budget still applies; tombstones are never silently discarded to pass it.
Relation IDs remain hashes of the original canonical authored endpoints, matching
validation and the append-only review registry; only effective endpoints resolve
through tombstones. Historical dangling references remain explicit rather than
inventing replacement nodes.

The owner approved routine independent review, while the original `Review`
schema had no agent provenance fields. Optional `kind: agent`, `session`,
`author_session`, `report`, `report_sha256` and `subject_sha256` extend effective
relation and evolution review records. Once `kind: agent` is present, all these
fields are required. Legacy review records remain readable. This extension does
not broaden permission to approve GitHub PRs, alter vocabulary without review,
or adjudicate unresolved mathematical/source disagreements.

## Reproducible local checks

```sh
uv run --project tools --extra serve pytest \
  tools/tests/test_retired_pipeline.py tools/tests/test_evolution_agent_review.py \
  tools/tests/test_public_tree.py tools/tests/test_index_site.py \
  tools/tests/test_evolution.py tools/tests/test_localdb.py
npm --prefix site test
npm --prefix site run lint
npm --prefix site run build
npm --prefix site run test:e2e
uv run --project tools python tools/scripts/check_fixture_site.py
uv run --project tools python tools/scripts/check_public_tree.py
uv run --project tools python tools/scripts/check_public_tree.py --repo ../homalg-horizon
```

The audit suite records its output under ignored `build/audit-*.log`. At handoff,
31 frontend unit tests and 16 browser tests pass, including the new historical
link workflow. The entry bundle remains about 144 KiB gzip. The existing default
2,000-node graph and real 100,000-node API browser measurements are documented in
[SITE.md](SITE.md); fully expanded and adversarial topology limitations remain
explicit.

## Optional doc-gen4 measurement plan

After the pilot reaches its required acceptance, use an isolated checkout of the
exact accepted commit and the pinned Lean/Mathlib toolchain. Pin a compatible
doc-gen4 revision there; record its SHA and the runner's hardware/cache state.
Do not edit the production Lake dependency graph or enable a scheduled workflow
merely to attempt the measurement.

1. Record the exact argv, Git SHA, toolchain and doc-gen4 SHA. Measure a cold
   documentation build with wall-clock timing and resource statistics; preserve
   exit status and complete build logs. Record any network/cache setup separately.
2. Count the complete documentation output bytes and generate the declaration
   name inventory `decls.txt` from the same successful build. Check a representative
   Lean declaration link and reject missing targets. Report both cold and warm
   measurements if a cached run is also measured; do not substitute the warm time.
3. Proceed only if the successful CI-equivalent build is at most 30 minutes and
   output at most 500 MB. Otherwise preserve measurements and leave doc-gen4 off.
4. Only after those gates pass, add the weekly SHA-pinned `docs.yml` workflow and
   commit-keyed Release assets, restore the latest accepted artifact under
   `site/dist/docs/`, gate declaration links against its `decls.txt`, and rerun
   `homalg site-data --check-budgets --dist site/dist` after restoration. Apply
   the same final publication preflight. The optional documentation must not
   bypass the overall Pages size budget or expose private source files.
