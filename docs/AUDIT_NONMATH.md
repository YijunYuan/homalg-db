# Non-mathematical requirements audit

Audit date: 2026-10-28. The core implementation and pilot publication are complete.
This audit covers implementation against requirements
version 1.0 and the owner's later independent-review policy, together with the
remote evidence explicitly recorded below. Both production progress snapshots
passed live verification, and actual submission created pilot PR #16, which
passed CI and merged. The subsequent repair PR #17 and exact-commit production
deployment passed the final data, interaction and visual acceptance.

| Area | Finding and evidence |
| --- | --- |
| M0 contracts | Schema checks and generated TypeScript preserve strict contracts. New optional retirement and review fields are described below; empty retirement registries do not change fixture output. |
| M1 retirement | Fixed a real mismatch: validation resolved moved/merged ids while global relation loading did not. `retired.py` validates registries and rejects duplicate ids/cycles. `relations.py` resolves endpoints and duplicate/self edges while retaining authored relation IDs and review keys. The global index retains permanent tombstones and rejects reuse of live ids. |
| M2/M7 historical navigation | Static and SQLite/API node/dependency requests resolve the same move/merge chains. Old node pages display reason/date/author and link to the live node; pruning and absent replacements retain an explanation. Search facets resolve historical tag/concept ids. Tests cover chains, cycles, stale targets, canonical payload equality and real browser navigation. |
| M3 publication readiness | Existing governance tooling previews labels, rulesets, ownership and repository settings before applying them. `check_public_tree.py` inspects tracked and normally addable files without staging or publishing. It rejects private/runtime paths, PDFs and symlinks exposing private/external targets, including force-added ignored files. Main and fork both pass after removal of a generated Lighthouse browser profile. |
| M4 engine | Existing null-harness integration, fork session tests, private snapshot recovery and dashboard reference containment remain the concrete local evidence. Local mocks alone do not establish publication acceptance. The published wheel was installed in fresh clones, and both real Claude Code and Codex STMT/PROOF sessions passed with a green submission PR and deployed two-proof fixture; see [COLD_START_ACCEPTANCE.md](COLD_START_ACCEPTANCE.md). |
| M6 review | Added explicit ordinary independent-agent evolution review under the tracked owner-enabled policy. Public source-checking reports, distinct sessions, subject/bundle hashes and report hashes are required; changed reports/assertions invalidate indexing. No human provenance is fabricated and GitHub owner approval remains unchanged. Vocabulary maintenance still uses its existing maintenance PR plus an actual independent report; it gains no automatic approval flag. |
| M7 API/security | Live API contract tests remain in `test_localdb.py`; immutable snapshot resources, exact identifier search, overview/chapter requests, truncation and CORS are exercised. Existing pinned-action/minimum-permission audit and dependency audit remain applicable. New publication-path checks cover a gap beyond the existing PDF-only rule. |
| Optional doc-gen4 | The tooling built, but the real cold documentation build reached its 30-minute cap with exit 124. Complete output size and GitHub CI timing remain unknown. Publication stays disabled; no size-limit failure is claimed. |

## Completed remote evidence and remaining scope

Production infrastructure [PR #15](https://github.com/YijunYuan/homalg-db/pull/15)
merged as `34ca001157dcccb99eb5878aac4e77be500af79e`. Both its
[Pages run 40642971475](https://github.com/YijunYuan/homalg-db/actions/runs/40642971475)
and [release run 40643093648](https://github.com/YijunYuan/homalg-db/actions/runs/40643093648)
completed successfully. The actual downloaded
[data archive](https://github.com/YijunYuan/homalg-db/releases/download/data-2026-10-28/data-2026-10-28.tar.gz)
has SHA-256 `da54d56fdf9bf4d02912b4606968cb4def7b8b4f02e4aefffc85888fb42e4ae3`,
62,389 bytes and 41 archive entries. LICENSE, LICENSE-DATA and NOTICE are present;
private paths are absent. The retained local verification is
`build/released-data-verification.json`. This snapshot contains the registered
pilot before its final node submission; it does not certify the completed pilot's
published proofs or live progress counts.

The separate [cold-start acceptance](COLD_START_ACCEPTANCE.md) passed M4-T4:
both actual CLI engines completed statement and proof tasks;
[acceptance PR #13](https://github.com/YijunYuan/homalg-db-acceptance/pull/13)
passed CI and merged through ordinary squash merge, and
[deployment 40643719471](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40643719471)
showed two proved nodes and `2 of 2 items proof complete` in a real browser.
That report retains the initialization-only bypass, dependency-cache reuse,
local private-backup destination and failed upstream-download retries. It also
states that no real two-account claim race or non-owner denial exercise occurred.
M4-T5 also passed for the first and final stable production status snapshots.
The final status `ad2ad1ad711004943066ece77332d7ad21de9544` reached
[deployment 40665487067](https://github.com/YijunYuan/homalg-db/actions/runs/40665487067).
The actual browser matched the complete remote status payload and observed
27 proof-complete items, ten reviewed pages, zero open human questions and a
green last check, with zero JavaScript, HTTP or request errors. This remains
labelled run progress over the pre-submission main registration.

The actual Codex Horizon run `0001` verified the already implemented first
chapter without source changes; its after-session hook succeeded and recorded
a successful backup. All 33 pilot tasks are now done. The actual normal submit
created [PR #16](https://github.com/YijunYuan/homalg-db/pull/16), head
`e4b0cd6c8bc7b85e6a02903292d003855cfbcf85`. Its
[CI run 40666512164](https://github.com/YijunYuan/homalg-db/actions/runs/40666512164)
passed, with a 3 minute 43 second Lean job. The standard REST squash endpoint
checked that exact head and merged as
`5b4771d924974ea59a9c4c1ec5bd5713af4e6482`. The CLI's preceding `BLOCKED` precheck
did not establish a cause. No administrator/force option or rule change was
used; no synchronization or non-owner-governance conclusion is inferred.
The main deployment passed. Its real data and interaction checks passed, while
visual review found the separate sparse-graph clipping defect described below.
[COLD_START_ACCEPTANCE.md](COLD_START_ACCEPTANCE.md) retains the session
and both status captures, including the earlier intermediate counts.

The follow-up commit `e219ce0` (rebased from `55234ff`) fixes empty escalation after submission:
with no eligible inbox candidates it returns success before the human guard,
GitHub client or confirmation prompt. Nonempty escalation retains the guard and
per-item confirmation. Positive/negative regression cases and the focused
39-test suite passed, followed by independent review. No GitHub issue or
notification was sent by these tests.

Both that fix and the sparse-graph repair shipped in
[PR #17](https://github.com/YijunYuan/homalg-db/pull/17), which passed
[CI 40670365185](https://github.com/YijunYuan/homalg-db/actions/runs/40670365185)
and merged as `c5489f42b97470d6424778a0b8134ed59c520d0a`. Lean was deliberately
skipped for the tool/site-only classification; deployment still built and
validated the complete library. The
[production deployment](https://github.com/YijunYuan/homalg-db/actions/runs/40670763457)
passed. At `2026-10-28T10:21:00.933Z`, all 17 browser assertions passed against
that exact commit, with zero JavaScript, HTTP or request errors. The 44-node
expanded graph fits inside the canvas, all six nodes' deviation explanations
render completely, and the final screenshots were visually inspected.
The earlier Fidelity blank capture was a wait-timing issue, not missing data;
the strengthened script explicitly waits for every explanation. Historical
failure evidence is retained alongside `build/acceptance-live-pilot-final.*`.

The normal claim release [PR #18](https://github.com/YijunYuan/homalg-db/pull/18)
passed CI and merged as `8fc87a9123aafaa67331b7c4a4f3d590882228be`; `claims` is
empty. This metadata-only follow-up does not change the software or mathematical
content verified above. Real two-account governance remains an explicit
acceptance gap rather than a conclusion inferred from these owner submissions.

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

The audit suite records its output under ignored `build/audit-*.log`. The newer
`build/final-infrastructure-tests.log` records 375 Python tests passed,
18 skips, one Starlette `httpx` TestClient deprecation warning, 31 frontend unit
tests passed and current fixture artifacts. Sixteen skips require the compiled
test opt-in and one requires the benchmark opt-in. The additional MiniSearch
parity test ran before `npm ci` in the fresh infrastructure checkout; it then
passed independently (`build/final-search-parity.log`). The successful
`build/pilot-engine-make-validate.log` records zero validation errors, eight
warnings explained individually in node notes, 14 context-dependent skips and
19 passed Lean smoke/export tests. Five additional real pilot tests passed in
`build/final-pilot-lean-tests.log`, for 24 tests across those suites. No warning
rule was suppressed. The full
data build has 61 nodes and 201 edges; artifact budgets and the 9.1 MiB site build
passed, with 144.1 KiB entry JavaScript gzip. The pilot accounts for 44 nodes,
29 source items, 13 confirmed foundations and three bridges; its source-item
headlines are 27 proof complete, one statement complete and one confirmed error.
The quotient corollary's valid local proof retains its source-only edge to false
Theorem 5.1, and seven cited nodes retain nine explicit external proof obligations.
After the graph-fit repair,
31 frontend unit tests and 19 browser tests passed, including historical links,
an actual 20,001-node/20,000-edge WebGL document render, PNG export, and a forced
WebGL-unavailable accessible fallback. The existing default
2,000-node graph and real 100,000-node API browser measurements are documented in
[SITE.md](SITE.md); fully expanded and adversarial topology limitations remain
explicit.

## Optional doc-gen4 measurement

The real isolated cold `lake build HomAlg:docs` run used accepted source commit
`5b4771d924974ea59a9c4c1ec5bd5713af4e6482`, Lean 4.35.0 and doc-gen4 commit
`0e1ffe2e4ba5ecfdfaf15c65b8d3805dbb7134ae`. It exited 124 at its 30-minute cap,
with a Python monotonic duration of 1,800.11 seconds. GNU time reported
`30:49.73`; the [measurement report](DOCGEN_MEASUREMENT.md) retains both raw
readings and the undiagnosed difference. No previous documentation artifacts
were reused; dependency cache preparation was measured separately. The build did not produce a complete
HTML artifact, so final output size and declaration-link coverage are unknown.
No size-limit failure was observed, and this local run does not verify the GitHub
runner's time gate. Production source, `lakefile.toml` and `lake-manifest.json`
were unchanged. Optional documentation publication remains disabled.

A future attempt must preserve the same evidence and publication gates:

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
