# Implementation and acceptance

The core implementation and pilot publication are complete. This checkout follows
the approved HomAlgDB requirements version 1.0 (2026-10-27); the table separates
delivered capabilities from the original acceptance boundaries still retained.
The owner's
[2026-10-28 amendment](REVIEW_POLICY.md) replaces routine human review gates with
independent agent reviews; only unresolved mathematical/source disagreements are
escalated.
The real two-account governance exercises and original per-page timing records
are still missing, so not every original acceptance item is claimed as passed.

| Milestone | Delivered implementation and evidence | Remaining acceptance or explicit boundary |
| --- | --- | --- |
| M0 | Public repository, pinned Lean/Mathlib, schemas, fixtures, CI and applied governance; independently reviewed initial vocabulary; consolidated regression passed | No outstanding local implementation check |
| M1 | Parsing, compiled exporter, index/artifacts, semantic checks and authoring commands; all 19 Lean smoke/export and five pilot acceptance tests passed; whole-pilot compiled validation has zero errors | Eight explained warnings and 14 context-dependent skips remain explicit |
| M2 | Blueprint, fidelity, search, claims, accessible views, static/API adapters and WebGL fallback; repaired production site passed all 17 final assertions and visual review | No outstanding pilot site acceptance |
| M3 | Registration, claim and infrastructure PRs merged; governance applied; Pages and data release passed; actual pilot submission PR #16, repair PR #17 and claim release PR #18 passed CI and merged | Real two-account governance tests not performed |
| M4 | Published fork v0.1.5-homalg.1 and both real CLI engines passed M4-T4; actual pilot Codex run and after-session backup passed; both production status snapshots passed M4-T5 | Cold-start cache and backup-destination limitations are recorded |
| M5 | Ten reviewed body pages; 44 nodes covering all 29 source items; 13 confirmed foundations and three bridges; independent reviews and all 33 planned tasks complete; compiled validation, remote CI and deployed-pilot acceptance passed | One confirmed source error and seven cited nodes with nine explicit external proof obligations remain visible; original per-page timings were not instrumented |
| M6 | Concepts/relations, global graph/timeline, provider adapter, import/review, cost guards and real two-source rehearsal; summary independently accepted; consolidated regression passed | Separately paid API execution is not claimed |
| M7 | SQLite/FTS5 API, static/API parity, 100k benchmark, partitioned search, graph overview, ledger concurrency and security documentation; bounded cold doc-gen4 measurement completed | Optional documentation stays disabled: the local build timed out at 30 minutes; complete output size and GitHub CI time remain unknown |

All advertised CLI commands are implemented; `homalg --help` is the current
command inventory. Unavailable context is listed in `summary.skipped`. A fast
validation run does not claim Lean, private-source or remote PR coverage that it
did not have. Human-only commands never fabricate approvals.

## Verification evidence

Local checks on 2026-10-28:

- Latest `make test` log (`build/final-infrastructure-tests.log`), from the
  isolated infrastructure checkout including the empty-escalation fix: 375 Python
  tests passed, 18 skipped and one warning; Ruff, generated TypeScript, frontend
  lint/format and 31 frontend unit tests passed. The warning is Starlette's
  deprecation notice for its `httpx` TestClient integration. Sixteen skips are
  compiled-test opt-ins and one is the opt-in large benchmark. The remaining
  MiniSearch/SQLite parity test ran before `npm ci` installed MiniSearch; its
  subsequent isolated rerun passed (`build/final-search-parity.log`). Site
  fixture artifacts match the committed raw-export golden.
- The successful `make validate` record is `build/pilot-engine-make-validate.log`:
  zero errors, eight warnings and 14 checks skipped for unavailable context;
  all 19 Lean smoke/export tests passed. Five additional real pilot acceptance
  tests passed in `build/final-pilot-lean-tests.log`, for 24 tests across those
  suites. Each validation warning is explained in its
  node's Formalization notes: four retained source dependencies exceed the direct
  compiled trace, and four conservative bypass warnings concern the intended
  comparison or homomorphism constructors. No validation rule was disabled.
- `make data` generated 61 nodes across three documents and 201 edges with all
  artifact budgets passing. `make site` produced a 9.1 MiB complete site and
  144.1 KiB entry JavaScript gzip. Logs are `build/final-data.log` and
  `build/final-site.log`.
- Browser suite after the graph-fit repair: 19 tests passed, including static navigation/accessibility,
  evolution rendering, actual SQLite API search/node/timeline/concepts, and
  chapter-scoped requests for a large document.
- Lifecycle/API focused suite: 46 tests passed. Temporary local Git remotes
  verify ownership, expiry, publication races, no force pushes, private snapshot
  recovery, idempotent attempts, three-stall blocking, scoped backups and sync.
- Fork suite: 506 tests passed before the published release. Its dashboard unit and
  browser tests passed; the wheel includes frontend assets and notices.
- `check_engine_integration.py`: two actual null-harness sessions invoked real
  HomAlg hooks and Lean exports in an isolated fixture checkout. The original
  `.git` and HEAD survived, the private ledger excluded private source, and all
  15 Fixture2000 nodes validated. Two no-progress sessions recorded two attempts.
- Actual blueprint import: 17 blueprint nodes, 17 linked Lean declarations and
  15 hard dependency edges, matching authored fixture headers. Additional graph
  edges are the expected blueprint-to-declaration links.
- The 100,000-node API benchmark built artifacts in 14.52 s and SQLite in
  19.08 s (1.10 GB). Measured API searches were 35.97–40.10 ms; 1,000-node chapter
  responses were 88.70–98.05 ms. Separate browser measurements passed on two
  consecutive runs: default collapsed 2,000-node graph first paint 464–468 ms,
  real 100,000-node SQLite overview 886–890 ms, selected 1,000-node chapter
  618–625 ms. Expanding all 2,000 nodes took 1.23–1.25 s; it is not the default.
- Actionlint and the repository workflow audit pass. Both frontend dependency
  trees and both Python lockfiles have zero findings in the recorded npm/
  pip-audit checks. `docs/SECURITY.md` records scope and limitations.

PR #16 also passed remote CI and merged. Repair PR #17 passed its applicable CI
and the final deployed-pilot browser acceptance passed against its exact merge
commit. Local tests, status publication and actual deployed-source checks are
recorded separately below. The acceptance commands are:

```sh
make test
make validate
make data
make site
# With the pinned fork on PATH:
uv run --project tools --locked --all-extras python tools/scripts/check_engine_integration.py
```

`make validate` performs real compiled validation and separately enables the
Lean smoke/export golden tests. `make site` compiles the actual application.
`make data` regenerates live public data and checks artifact budgets. The fixture
freshness check intentionally uses committed fixture-only inputs and the raw Lean
golden, so ordinary unit tests do not load the private literature repository or
depend on an in-progress real paper.

## Pilot evidence and honest boundaries

`Hochschild1945` uses the exact supplied 11-page PDF with SHA-256
`f2ac1d8408922a2445f27b358113de71db769609482da3626c5eddfe64277b19` and
`page_offset: -56`. The private copy is in the user's separate Git-LFS repository.
Rendered pages and extracted navigation text remain ignored. PDF pages 2–11 were
transcribed from images, cross-reviewed by independent agent sessions, and are
hash-bound satisfactory records. The cover is outside the mathematical task.

The review caught a footnote page-range error, a missing kernel symbol and an
equality/congruence error. Two suspected page-10 errors were resolved as false
positives with a larger rendering. Per-page elapsed times were not instrumented
and must not be reconstructed as invented measurements. The correction record
is real evidence, not an accuracy estimate for unseen material.

All 29 specified source ids have been inventoried, including footnote H0 and
unnumbered constructions. Page completion waits for every referenced node.
Reviewed transcription is distinct from fidelity review of the Lean statement.
The source's finite-dimensional nonunital algebra is retained; no automatic
unital-algebra assumption or human confirmation is introduced. The current
13 foundation entries have independent agent confirmations under the approved
policy. Each record includes the author/reviewer sessions and a content hash;
no human confirmation was invented.

All 33 planned pilot tasks are done. The 44 compiled nodes include the 29 source
items, three bridges and seven cited nodes. The source-item headlines are
27 proof complete, one statement complete and one confirmed error. The
statement-complete item is `Cor_quotient_separable`: its repaired local proof is
complete, but its faithfully retained source-only edge to the false Theorem 5.1
keeps the global headline conservative. The seven cited nodes retain nine
explicit external `sorry` boundaries; these are not counted as proved background
theorems.

## Remote publication evidence

The public [database repository](https://github.com/YijunYuan/homalg-db) and
[engine fork](https://github.com/YijunYuan/homalg-horizon) are published. The fork's
[v0.1.5-homalg.1 release](https://github.com/YijunYuan/homalg-horizon/releases/tag/v0.1.5-homalg.1)
contains the wheel, installed into fresh environments and exercised with real
engine sessions. Fork CI passed, including both supported Python versions.
Production registration and claim PRs passed CI and merged.

Production infrastructure [PR #15](https://github.com/YijunYuan/homalg-db/pull/15)
merged as `34ca001157dcccb99eb5878aac4e77be500af79e`. The matching
[Pages deployment](https://github.com/YijunYuan/homalg-db/actions/runs/40642971475)
and [data-release run](https://github.com/YijunYuan/homalg-db/actions/runs/40643093648)
succeeded. The site is at
[yijunyuan.github.io/homalg-db](https://yijunyuan.github.io/homalg-db/).
The published [data-2026-10-28 release](https://github.com/YijunYuan/homalg-db/releases/tag/data-2026-10-28)
contains the actually downloaded and inspected
[data-2026-10-28.tar.gz](https://github.com/YijunYuan/homalg-db/releases/download/data-2026-10-28/data-2026-10-28.tar.gz):

| Check | Observed result |
| --- | --- |
| SHA-256 | `da54d56fdf9bf4d02912b4606968cb4def7b8b4f02e4aefffc85888fb42e4ae3` |
| Compressed bytes / archive entries | 62,389 bytes / 41 entries |
| License files | LICENSE, LICENSE-DATA and NOTICE present |
| Private paths | Absent |
| Snapshot commit | `34ca001157dcccb99eb5878aac4e77be500af79e` |

The local inspection record is `build/released-data-verification.json`. This is
the infrastructure snapshot with the registered pilot before its final node
submission; it is not the completed pilot's formalization release.

The actual `homalg submit Hochschild1945` created production
[PR #16](https://github.com/YijunYuan/homalg-db/pull/16), head
`e4b0cd6c8bc7b85e6a02903292d003855cfbcf85`, using the existing claim. Submission
rebuilt and validated the document in an isolated worktree and backed up the
committed source. Its
[CI run 40666512164](https://github.com/YijunYuan/homalg-db/actions/runs/40666512164)
passed, including the Lean job in 3 minutes 43 seconds. The CLI merge precheck
reported `BLOCKED`; the standard REST squash endpoint subsequently accepted the
exact expected head SHA, producing
`5b4771d924974ea59a9c4c1ec5bd5713af4e6482`. No administrator/force option or rule
change was used. The precheck did not establish why it refused, so no
synchronization explanation or non-owner governance conclusion is inferred. The
[deployment 40667644896](https://github.com/YijunYuan/homalg-db/actions/runs/40667644896)
passed. Data and interaction checks passed, but screenshot review found that
the expanded graph clipped a long sparse layout; that issue has a separate
repair and deployed acceptance below.

[Repair PR #17](https://github.com/YijunYuan/homalg-db/pull/17) includes the
empty-escalation fix and graph-fit repair. Its
[CI run 40670365185](https://github.com/YijunYuan/homalg-db/actions/runs/40670365185)
passed classification, checks and gate; Lean was deliberately skipped because
these tool/site changes have `needs_lean=false`. Owner approval also passed.
It merged as `c5489f42b97470d6424778a0b8134ed59c520d0a` through the same standard
exact-head REST squash operation, without administrator/force options or rule
changes. Superseded opening/label-event runs were cancelled, not failed checks.

[Deployment 40670763457](https://github.com/YijunYuan/homalg-db/actions/runs/40670763457)
passed, and the real production browser acceptance completed at
`2026-10-28T10:21:00.933Z` against that exact manifest commit. All 17 assertions
passed with zero JavaScript, HTTP or request errors. All 44 expanded graph nodes
fit inside the viewport; the overview, chapter, list and Fidelity screenshots
were visually checked. All six nodes' deviation explanations loaded completely.
Search, proof details, the confirmed source error and the corollary's dependency
boundary were verified on the public site. Evidence is retained in
`build/acceptance-live-pilot-final.*` and the
[cold-start report](COLD_START_ACCEPTANCE.md#final-repaired-deployment-acceptance).

The normal `homalg release Hochschild1945` also completed:
[PR #18](https://github.com/YijunYuan/homalg-db/pull/18) passed its
[CI run 40671666694](https://github.com/YijunYuan/homalg-db/actions/runs/40671666694)
and owner check, then merged as `8fc87a9123aafaa67331b7c4a4f3d590882228be` at
`2026-10-28T10:25:14Z`. The claim file has `claims: []` and no review request was
created. Its [deployment 40671979915](https://github.com/YijunYuan/homalg-db/actions/runs/40671979915)
passed; a real manifest fetch at `2026-10-28T10:31:39.271Z` confirmed the exact
merge commit, `claim.state: unclaimed` and unchanged 27/1/1 source headlines
(`build/final-release-live.json`).

The separate [cold-start report](COLD_START_ACCEPTANCE.md) records passed M4-T4:
real Claude Code and Codex each completed statement and proof tasks from fresh
clones using the release wheel. The actual submission
[PR #13](https://github.com/YijunYuan/homalg-db-acceptance/pull/13) passed
[CI](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40642480584)
and merged normally as `4e96a3939cb0f6c39bd841b485ede6eec9f18745`.
Its [Pages deployment](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40643719471)
passed, and a real browser observed two proved nodes, zero planned nodes and
`2 of 2 items proof complete`, with zero JavaScript errors or failed responses.
The report preserves its narrower scope: shared dependency cache, local private
backup, initialization-only administrator bypass and no two-account governance
exercise.

Production M4-T5 passed using the existing pilot claim. The first status
`e268134aff210abf306872cd2b2bf45e0f4dac51` reached
[deployment 40645173934](https://github.com/YijunYuan/homalg-db/actions/runs/40645173934).
The final stable status `ad2ad1ad711004943066ece77332d7ad21de9544` reached
[deployment 40665487067](https://github.com/YijunYuan/homalg-db/actions/runs/40665487067).
A real browser compared the complete deployed status with the remote payload
and observed `27 proof complete · 10 pages reviewed · 0 questions for a human`,
a green last check, PROOF 6/6 and STMT 12/12, with zero JavaScript, HTTP or request
failures. Both deployments still used the pre-submission main registration;
the displayed run progress was explicitly separate from CI-validated published
formalization. Historical first-capture counts were not rewritten.

The actual Codex Horizon run `0001`, session
`0002-horizon-Hochschild1945.PROOF.1`, verified the already implemented first
chapter without changing source. Its after-session hook returned zero, marked
the task done and recorded `backed_up: true`; its automatic status publication
was throttled. The remaining chapters subsequently passed their normal stage
commands. This is final-verification evidence, not a claim that one session
authored all pilot proofs. The [cold-start report](COLD_START_ACCEPTANCE.md)
retains the exact session, hook and browser evidence.

The follow-up fix `e219ce0` (rebased from `55234ff`), merged in PR #17, makes
escalation with no eligible inbox
candidates a successful no-op before constructing a GitHub client, prompting or
requiring a human session. Nonempty escalation still requires the original
human guard and per-item confirmation. Focused regression tests passed, and an
independent reviewer checked both branches before publication. This behavior is
included in the deployed repair; no issue was published by the regression tests.

No reviewer was requested for the implementation PRs. At the owner's request,
Dependabot version-update PRs were closed and automatic version-update creation
was paused in PR #14; ordinary validation remains enabled.

The real evolution rehearsal uses the 1945 pilot and independently inspected
primary-source pages from Hochschild's 1942 paper. Its generated summary was
accepted by an actual independent root-agent review of the exact subject and
bundle, recorded in [the public report](evolution/independent-review.md).
The model identifier was unavailable and is recorded as `not-reported`; no
provider usage or cost is invented. A repeat import created an unreviewed new
version while preserving the older accepted version. The second paper is not
inventoried in the live registry, so this is an isolated, reproducible rehearsal.
See [evolution evidence](evolution/README.md) and its reviewed snapshot.

The owner explicitly confirmed Theorem 5.1's source error after independent
counterexample reviews. Its original claim, named unproved theorem and open,
confirmed dispute are retained. This does not constitute approval of a corrected
replacement theorem. A genuine quotient-annihilator construction is isolated
from the false claim, and the following corollary has a complete local repaired
proof with an explicit proof-route deviation. Theorem 4.1 now also has a complete
local proof, and final independent review, export, validation and proof-stage
acceptance passed. Seven classical citation nodes retain nine explicit external
proof obligations; neither fidelity locks nor local proof completion claim
proofs of those background results.

## Specification decisions

1. **Generator version.** R7.4 names an integer internal constant, while A.1
   requires a serialized string. Keep the integer and serialize `str(version)`.
2. **Pinned native evaluation.** Lean v4.35.0 emits generated
   `native_decide.ax_...` axioms; `Lean.ofReduceBool` does not exist there. Test
   the required nonstandard-axiom property rather than the obsolete spelling.
3. **Lexer provenance.** The specified SHEAF revision has no license or lexer
   tests. Its segment contract was inspected; the implementation is independent.
   Standard bang/dbg_trace interpolations are covered. Arbitrary user-defined
   syntax that changes lexical string rules is outside this lightweight lexer.
4. **Synthetic evidence.** Fixture reviews, claim dates and human names are
   explicitly fictional. The fixtures exercise complete/reopened/disputed states
   without granting any approval to a real paper. An additional proved auxiliary
   supplies M1-T4's required dependency assertion without changing the intentionally
   unproved lemma used by the pending-dependency fixture.
5. **Exporter extensions.** Optional global-instance/own-document instance-type
   information and external-constant existence records support the specified
   semantic checks. Local derived records continue to exclude global axiom closure.
6. **Evolution contracts.** Normative §7.4 needs computed bundle hashes/staleness
   beyond A.8. The index concept record has an optional computed hash; stale flags
   live in the site evolution projection, never in authored concepts. The optional
   graph `via_aux` and `previous_edition` behavior are implemented and tested.
7. **Artifact extensions.** Optional prerender search-option hashes and
   per-document serialized search-index paths support freshness and large static
   search. Legacy global search artifacts remain readable. Cleanup removes only
   validated files referenced by the previous manifest, preserving unknown files.
8. **Hollow-definition allowance.** The requirement names an allowance file
   without defining its shape. The implementation accepts explicit allowances
   with a node, reason and satisfactory reviewer/date evidence; no blanket bypass.
9. **Blueprint order.** The specification references an undefined authored
   `order` field. Use inventory order, then source coordinates/natural ids,
   without silently adding an authored field to the strict node schema.
10. **Contrast.** Pale status fills cannot themselves provide 3:1 contrast against
    white. Accessible outlines/non-color cues provide the required control contrast;
    text uses at least 4.5:1. These are separately checked from the fill palette.
11. **Fork base.** The explicitly requested upstream commit is `da5e685`;
    upstream tag `v0.1.5` points to its parent `5d603f8`. The fork follows the
    explicit commit and records this discrepancy in `UPSTREAM.md`.
12. **Chapter-only article.** The generic `new-node` text requests both chapter
    and section whenever structure exists, but the pilot explicitly has no child
    sections. Require a known chapter and require section only when that chapter
    declares sections. This preserves the approved pilot representation.
13. **Cross-page provenance.** Private page provenance comments and appended
    footnotes must not interrupt a source paragraph spanning pages. Comparison
    joins reviewed bodies and retains footnotes separately; mathematical tokens
    and the underlying reviewed bytes/hashes are preserved.
14. **Historical summaries.** A before/after review summary can report committed
    local proof/fidelity/lock facts from `nodes.json`. It labels them as local;
    it cannot invent historical global headlines without the old complete export.
15. **Optional doc-gen4.** The tooling built successfully, but the actual isolated
    cold `HomAlg:docs` build exited 124 at its 1,800-second cap. The
    [measurement report](DOCGEN_MEASUREMENT.md) preserves both elapsed readings:
    1,800.11 seconds from Python's monotonic clock and `30:49.73` from GNU time;
    their discrepancy was not independently diagnosed. It did not produce a
    complete documentation artifact, so final
    size and link coverage remain unknown; no size-limit failure is claimed.
    This local run also does not establish GitHub runner timing. Production
    dependencies and source were unchanged, and optional documentation remains
    disabled. Its optional status does not waive the required core pipeline,
    site or mathematical acceptance.

## Provenance of contributor-authored support nodes

The requirements' `statement-provenance` exemption list did not mention auxiliary
and bridge nodes, although M5 requires new comparison theorems absent from the
historical paper. The implementation therefore restricts verbatim paragraph
comparison to source-item statements and skips nodes with `aux` metadata,
including bridges. Their parent, source anchors, dependency and compiled-witness
checks still apply. Verbatim cited statements remain checked; only explicitly
editorial citations have the existing citation exemption. A regression exercises
all four cases against reviewed private page hashes.

## Workflow optimization verification (2026-11-04)

This is a source update developed from main `0975e717`, with fork instruction
sources based on `df21eed9a35ff3e87dde4f1031d66ee83508392b`. It does not revise the
historical acceptance above or assert that an older published wheel contains the
new instructions. The complete local checks below ran against source-ledger
revision `07918961bed4584f611d3bc8b2b406d5b78ee9d5`, including runtime revision
`e016d483c8bd4b9c4127a875de824ee515575205` with the registration-cache fix. The revised fork instructions are
recorded separately at local ledger revision
`15430cf32fae1e62cb83934689328e2be4c44ec9`. These are local tested revisions, not
claims that those commits or updated packages have been published remotely.
Subsequent documentation-only commits record these results without changing the
tested runtime. Publication must identify its own released revision.
See [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md) for the executable sequence.

Implemented changes cover isolated draft ownership/check/promotion/retirement,
frozen author handoffs and final report snapshots, fresh per-node batch fidelity
registration, and read-only next-task recommendations with persisted proof mode.
Individual reports, actual identities, protected human fields, input freshness,
private/scope boundaries and final stage/session evaluation remain required.
Preflight reports explicitly defer derived-cache freshness checks; it is not a
replacement for final repository validation. Multi-file integration/registration
uses recovery journals rather than claiming instantaneous filesystem atomicity.

The following bounded measurements used synthetic fixture inputs and retained
actual tool output:

- `build/workflow-batch-smoke/final-result.json` (SHA-256
  `4ba32c37ca564208394b7bfbea3738863555852a6f90a43bdaa0d4d37d152996`):
  this earlier implementation round, before the subsequent receipt fix, recorded
  a 5.54 s warmup. Two-node batch registration took 10.55 s with one real
  Lake build and one exporter invocation; sequential single-node registration
  took 25.78 s with two of each. Lock payloads matched. This is one warmed fixture,
  batch measured before sequential runs, not a literature benchmark or a general
  speedup estimate. Identity values were explicitly fictional fixture provenance,
  not mathematical approval of live nodes.
- `build/workflow-batch-smoke/workflow-result.json` (SHA-256
  `4a443cd6460d03183e590279c2d5385b9ab6eb5ccf26005dc89276a469a425b9`):
  the later implementation, including the receipt fix, completed real
  `prepare → verify → fixture reports → review-snapshot → batch → verify`.
  A deliberately mismatched author was refused before a fresh snapshot and the
  successful batch. Preparation took 10.73 s and registration 12.77 s, with a
  fresh Lake build/export in each phase. Validation findings were empty; the two
  derived-cache consistency rules were explicitly deferred and other unavailable
  checks remained listed as skipped. The author handoff remained valid after
  reports/authorized lock registration, and the task bytes were unchanged.
  This was a cached synthetic fixture with explicitly fictional review identities,
  no native session, no live literature approval, and no universal speedup claim.
- `build/workspace-rehearsal/report.json` (SHA-256
  `204b9a995a70d0db87fba4a1eca347d80fff36d204f71b73542dc10d3112e331`): two actual Horizon `0.1.5+homalg.1` /
  Lean `4.35.0` checks had overlapping recorded intervals and separate build paths
  and lock inodes. Sequential promotion integrated only the respective owned
  files; an unrelated prior promotion did not invalidate the second worker.
  The user's Git HEAD and index were unchanged. Failed setup/compilation attempts
  and the earlier report were retained; the latest stricter-input rerun passed.
- Documentation verification checked the actual command tree/help, internal links
  and task-template fields. The fork's role compilation, skills and common HomAlg
  instruction tests passed (17 tests). These checks validate installation text
  and command contracts; they do not establish mathematical fidelity or live
  project acceptance.

An integrated `make test` run completed with 504 Python tests passed, 17
skipped and one Starlette/httpx deprecation warning, plus 38 site tests;
`make site` also passed. These historical results preceded the registration-cache
fix below and remain in
`build/workflow-validation/make-test-before-registration-fix.log`. Skipped checks
remain explicit rather than counted as exercised coverage.

Full `make validate` exposed a registration-contract mismatch: a document can be
registered with only `document.yaml` and `claim.yaml`, before any node module or
`nodes.json` exists. The validator now reports per-document coverage skips
`nodes-json-fresh:KEY:no-node-modules` and
`nodes-json-stale:KEY:no-node-modules` only when there are genuinely no node source
files and no existing node cache. It does not manufacture an empty cache or a
mathematical result. Once any node source exists, even a malformed first header,
or any old/invalid cache remains, that exception does not apply. Missing cache,
bad headers and a leftover cache after deleting all nodes still receive the
ordinary findings; the fast stale check also compares the complete node-ID set.
All other applicable document/schema/source checks remain enabled. This is
separate from author preflight's explicitly deferred cache consistency rules.
The fix changes infrastructure only, not registered literature or mathematical
source files.

Final checks on the local tested revision above passed:

- `make test`: 509 Python tests passed, 17 skipped and one existing Starlette/httpx
  deprecation warning; all 38 site tests passed. Workflow security, Ruff,
  formatting, generated types, lint and fixture checks passed. The complete log
  is `build/workflow-validation/make-test.log`.
- `make validate`: exit 0 for four documents and 61 nodes, with zero errors,
  eight previously explained Hochschild warnings and 17 explicit coverage skips,
  including the two per-document metadata-only cache skips. All 19 actual Lean
  smoke/export tests passed. See `build/workflow-validation/make-validate.log`;
  the original registration failure and interrupted attempts remain separately
  preserved in that directory.
- `make site`: exit 0 with artifact budgets passing, 145.0 KiB entry JavaScript
  gzip and a 4.4 MiB generated site. This measures the local artifact, not a new
  remote deployment or a literature acceptance run.

These results establish local infrastructure acceptance at the recorded source
revision. They do not resume paused mathematical work, publish the new code or
approve any live node. Local ignored logs remain audit evidence; private sources,
worker state and fictional fixture reports are not public review locks.

## Source-ledger backup routing repair (2026-11-04)

The later run0012 after-session hook exposed a legacy limitation: `homalg backup`
created a discussion-archive commit in the user's ordinary Git even though the
engine had a separate source ledger. A subsequent backup network failure did not
undo that local commit. The user history was retained, not reset. Earlier
statements about unchanged user HEAD/index remain evidence for their stated
worker tests and checkpoints; they do not establish preservation during run0012.

The narrow fix is recorded at local source-ledger revision
`aa869dc88c7b933cbe4b9c8bc1a21702823de2ae`, authored by `/root/task_inventory`
and independently reviewed by `/root/ce_registration_review`. It changes only
`tools/homalg/lifecycle.py`, its publishing tests and the
[ENGINE publication boundary](ENGINE.md#publication-boundary). The frozen runtime
SHA-256 is `42a3ca3012b9ecb95b87268375441b9601c44848d4ec80235f5d406fe117a887`.
This records locally tested source, not remote publication or live installation.

With a valid `.archon-horizon/vcs/workspace.git`, archive/status/add/commit/push
operations use that ledger explicitly and push its pinned source commit. User
Git is queried read-only for remote configuration. Only changed owned-document
archive paths are committed; unrelated staging is preserved. Without a ledger,
the ordinary user-Git backup path remains; invalid/symlinked ledgers and inherited
repository/index redirection are refused. Private-source branch lookup and push
run separately in the private checkout. A work-backup remote must resolve to one
push target, distinct from all configured public-origin fetch/push URLs. These
checks do not certify remote visibility, permissions or universal URL equivalence.

All pushes remain non-forced. A non-fast-forward result retains the source commit,
reports `backed_up: false`, `reason`, `operation`, `source` and `source_commit`, and
does not record a successful throttle stamp. An earlier successful private-source
push can remain after the work-backup push fails. General Git clients, claims,
submission, numeric status and mathematical/task gates are unchanged.

The original implementation was actually run against the new temporary dual-Git
regression and failed its user-HEAD preservation assertion. Independent review
then found a second defect in the first fix: separate public-origin fetch/push
URLs could route fictional private discussion data to the public push target.
The revised guard compares all origin URLs and rejects multiple backup targets.
The identical probe now fails before archival with the expected destination
error. Both earlier failures remain recorded; the intermediate 519-test result
is not substituted for final-version acceptance.

The independent reviewer ran 15 focused backup tests and four additional actual
local Git scenarios: public-origin push-target refusal with no public refs;
private push failure with the correct operation and no success stamp; work push
failure retaining an earlier successful private push; and a successful distinct
private backup push URL. Each checked user HEAD/index/config preservation and a
source ledger without remote configuration. This is technical code review and
local Git integration, not mathematical review, live authentication or a
performance benchmark.

Final verification at the frozen revision passed:

- `make test`: 523 Python tests passed, 17 skipped and one existing Starlette/httpx
  deprecation warning; 38 site tests passed. Security, Ruff, formatting, generated
  types, lint and fixture checks passed. The focused publishing/lifecycle suite
  separately passed 39 tests.
- `make validate`: exit 0 for four documents and 61 nodes, zero errors, eight
  existing Hochschild warnings and 17 explicit coverage skips; all 19 actual Lean
  smoke/export tests passed. Skips remain unavailable coverage, not successful
  execution of those checks.
- `make site`: exit 0 with budgets passing, 145.0 KiB entry gzip and a 4.4 MiB site.
  This is a local artifact check, not a remote deployment or speed measurement.

The following ignored local evidence is identified by path and SHA-256. These
paths are not public artifact links:

| Local path under `build/backup-ledger-fix/` | SHA-256 |
| --- | --- |
| `final-report.json` | `237bec7171efaa789f148642a73cff3e2b99ec1523753d53cc7b2798fab19370` |
| `make-test-origin-guard.log` | `99fd0de184402a3ab79b2121b2a568254b7860a0c0ef390287b7c3f5ce9edea0` |
| `make-validate.log` | `318225e9fd91e03a1daad791bf1cae05e1464a768a0ca39ad55391d0feb643c1` |
| `make-site.log` | `edb64f47fd5ae7f610da718b09cc71ab96082874edc08d19ba49278a5e7ca289` |
| `baseline-reproduction.log` | `f89a8166d11303ec09be605d6da432b70d218507879033a9a4dbd235adf3555f` |
| `independent-ce-review/review.json` | `612002fb9aa4a1e069e5a45f071227bf5821e1679b4adfe02825b5295a1c0291` |
| `independent-ce-review/additional-cases-result.json` | `6dcdc84b98fe3cb440495fe4d1fccd66e06cc95b6d95304b839820ff7dc85034` |

The independent report binds exact runtime/test/ENGINE bytes and the original
push-URL reproduction plus its rejection log. The implementation checkout's user
HEAD/index also remained unchanged through the fix's ledger-only commit. These
results do not assert live installation, successful production backup, completed
T7 recovery or acceptance of any CE source or mathematics; those operations need
their own actual receipts.

## Call-local planning and claim-history inputs (2026-11-04)

The subsequent performance investigation identified repeated reads inside ordinary
planning and validation. The recorded T7 hook lasted 512.781 seconds, but its
timestamps do not isolate planning: the 277-second interval between the validation
report and entry into status publication also includes other hook steps. These
observations are not a measured whole-hook speedup.

The narrow implementation by `/root/task_inventory` changes input reuse only:

- A validation `Context` resolves each document's already-fetched status branch
  to an explicit object id and reads that immutable history once. An absent ref
  is retained as absent for that context. A new context observes later refs and
  uses its own schema store. There is no process-global or persistent history
  cache and no network fetch. Every node still receives its scope test; claim,
  policy, evaluation time and expiry are recomputed from the current context
  inputs. Existing tracked-node/user-Git semantics and invalid-history handling
  remain unchanged. Standalone history readers also use a pinned object id for
  their individual read, avoiding mixed histories if a ref advances mid-read.
- Each `unlocked_tasks` call reads the document's authored node headers and
  inventory occurrence ranks once. Each candidate retains the original primary,
  cited and immediate-auxiliary selection, then sorts only those selected nodes
  by the original source-order rules. T and INV candidates retain their full
  `node_ids`, including the `node_list` consumed by task templates. A new planning
  call or standalone `scope_nodes` call rereads source and inventory inputs.

Task completion evaluation, fast/full validation, transcription reconciliation,
proof deferral, review gates and all three export input snapshots are unchanged.
The implementation does not cache validation verdicts across stages or derive
approval from a cached input. It does not modify a user's Git history to change
which nodes count as tracked.

The first focused test run exposed a Git compatibility error: `show-ref --hash`
without `--quiet` reports an absent ref differently. That failed run is retained.
The revision preserves the original quiet presence check, then resolves the ref
before reading history. Regression tests use actual temporary Git repositories
and cover advancing/missing refs, fixed-commit reads, independent contexts and
documents, schema changes, malformed history and claims, per-node scope changes,
all task kinds and template objectives, refreshed source/inventory inputs, and
read-only workflow recommendations with proofs deferred.

An isolated benchmark loaded the old modules directly from source-ledger revision
`333403f9c8fadd5454e044d0733fa6470cfa28e0` and compared them with the frozen
candidate on fictional inputs. Three alternating pairs produced identical
proposals and scope findings without changing fixture source bytes:

| Measured operation | Old median | New median | Work counted per invocation |
| --- | --- | --- | --- |
| Proposal construction, 156 nodes, 18 chapters, 77 T chunks | 61.822 s | 0.425 s | Header reads/parses: 25,584 to 156; inventory reads: 164 to 1; all 108 returned proposals identical |
| Scope rule, 156 nodes, five local status commits | 2.182 s | 0.262 s | Git subprocesses: 1,092 to 8; all 156 scope findings identical |

These are local microbenchmarks, not measured CE hook improvements. The proposal
benchmark supplies fixed fictional transcription states and missing task records
to isolate construction; production prerequisite validation is unchanged. The
runs share one process and uncontrolled operating-system caches/CPU contention.
The reproducible script, exact baseline modules, raw paired samples and parity
assertions are retained under ignored `build/planning-read-optimization/`.

Independent reviewer `/root/locate_wiki` tested the frozen runtime and regression
test bytes against the exact baseline modules. Forty targeted repository tests,
eight independent composite cases and three supplemental cases passed. They
include 28 exact stage/objective comparisons, ten prerequisite/foundation/early
review variants, actual dual-Git tracking and ref races, malformed/empty T and INV
inputs, and matching fast/full-no-build findings and skipped coverage. The
independent smaller benchmark also preserved all 19 prerequisite evaluations
while reducing repeated source reads. No reviewer edited the implementation.

Required acceptance completed in the isolated implementation checkout:

- `make test`: exit 0; 542 Python tests passed, 17 skipped, and 38 site tests
  passed. The existing Starlette/httpx warning remains. This run's `npm ci`
  reported 12 moderate dependency advisories; dependency lockfiles were not
  changed and no dependency upgrades or audit fixes are included in this work.
- `make validate`: exit 0; zero errors, eight existing warnings and 17
  context-dependent checks skipped, followed by all 19 actual Lean smoke/export
  tests passing. Skipped checks are unavailable coverage, not successful checks.
- `make site`: exit 0; budgets passed at 145.0 KiB entry gzip and a 4.4 MiB site.
  The first complete site log was preserved, then this target was repeated once
  to capture its actual exit receipt after the original tool response was
  truncated. This was missing receipt recovery, not an implementation failure.

The final local evidence is retained under ignored
`build/planning-read-optimization/`; these are local paths, not public downloads:

| Evidence | SHA-256 |
| --- | --- |
| `benchmark.py` | `61d97f83a4eb198419a6cfda0f541585857a0f85b1e2394d994acf247f04aaef` |
| `benchmark-result.json` | `9d342cfde1e4aec0069742bb98cce38f9c93feeceaa77bdb12ec0f8527c339f8` |
| `independent-locate_wiki/review.json` | `4cbedd6bb05997f0aeaffe7fb13ed87f504a92ee8b1c0ce8f06139348a1fc337` |
| `make-test.log` | `35c554f6f7eff80c643d0524d60472614d556b2075cab2e580e3adf5a1f66d2e` |
| `make-validate.log` | `5ccf9d1f74ddd948ae9892605c7d4f71cff2c2cfb09089701e915408ae1877ad` |
| `make-site-receipt.log` | `5653ad33083601f7b41781641ddd42029a4c1af064fb5737eb208a3124e8f55c` |
| `make-site-receipt.json` | `63b9e4e5dc450f7e622f2e5eeed20fbc85d419e9e4dd70dfd5426e655ff86912` |

The implementation checkout's user Git HEAD and index remained unchanged.
This acceptance establishes the narrow tooling change and synthetic parity; it
does not assert deployment, a measured production hook speedup or acceptance of
any CE source or mathematics. Live book work still requires its ordinary checks,
independent reviews and session hooks.

## Scheduling repair acceptance (2026-11-04)

The local workflow repair adds opt-in statement-frontier planning and batches of
up to four independent author groups, preserving existing task scopes and all
source, DAG, compiled, fidelity and final-session obligations. Already accepted
groups are excluded from fresh authoring; chapter aggregates cannot be completed
by one small unit. Local blockers hold only the units that consume those inputs.

Native Horizon can create source-only isolated workers during its own serial
session, collect frozen candidates with baseline/dependency/scope checks, and
compile/review them at its canonical boundary. Collection explicitly grants no
compile or review approval. External draft integration still requires an idle
workspace and successful worker checks. Workers receive fresh public-only ledgers;
runtime configuration and its historical Git objects are not copied. Worker
commands remove inherited canonical Git/session routing and honor the pinned
Horizon executable. A native lead cannot invoke the external after-session hook.

The matching local fork honors task priorities and dispatch holds, does not blindly
repeat blocked tasks, records outer-hook failure before publishing completion,
keeps unit completion separate from aggregate roadmap completion, writes task
snapshots atomically, and terminates verified Linux run descendants when stopped.
Its source remains versioned `0.1.5+homalg.1`; installed file hashes, not that
unchanged version string, identify this repair. No new public release is implied.

Completed infrastructure checks, with logs under `build/scheduling-repair/` in
the respective implementation checkouts:

- HomAlg `make test`: 570 Python tests passed, 17 skipped, one existing warning;
  all 38 site tests and fixture/type/lint/security checks passed. This full run
  preceded the final accepted-group scheduling filter; its separate 21-case
  frontier regression covers that final change.
- HomAlg `make validate`: zero errors, eight existing warnings and 17 explicit
  context skips; all 19 real Lean smoke/export tests passed.
- HomAlg `make site`: passed with artifact budgets unchanged.
- Horizon full Python suite: 527 tests passed; its actual dashboard frontend
  also built successfully.
- Independent native-worker review added negative tests for protected reviews,
  scope, build locks, task mutation and inherited Git routing. The combined
  workspace/lifecycle suite passed 66 tests before the final scheduler filter.
- An actual CE source-ledger projection probe completed in 3.79 seconds, including
  explicit worker retirement. It excluded runtime files/history and Lake caches,
  and preserved the user Git HEAD, index and config. It authored no mathematics.

The paused CE run `0016` remains interrupted. Its retained source audit interval is
`82b5cfec045b3c1f0450f24b760a5402af29abf1` through
`5125d5c733bfba191239e804ce21078d954e142a`. A new native recovery must audit that
interval separately from its new session boundary. The live-layout probe and
infrastructure tests do not establish Chapter III formalization throughput or
mathematical acceptance; live outcomes have separate receipts under the CE
checkout's `build/workflow-scheduler-repair/`.

The real run `0017` then produced four independently authored candidates and
checked all four exact files in the warm canonical compiler lane within about
nine minutes. Collection exposed an additional live-layout defect: ignored
private `literature/<Doc>/ingest.yaml` was incorrectly counted as new public
validation context. The narrow classifier repair excludes that private file
from public context enumeration while refusing a source snapshot that tracks it.
All 50 workspace regression tests passed, including that live-layout scenario;
the first failed test assertion and corrected fixture are retained in the logs.

At the idle repair boundary, all four candidates were frozen and their old worker
leases retired without deleting evidence. Native run `0018` created current
workers with the original author identities, transferred only those exact bytes,
and collected all four into canonical Chapter III files. All four canonical
module builds passed with `reused: false`; SHA checks bind those builds to the
frozen candidates. They contain 28 header-listed main declarations, plus helpers.
The actual receipt is `build/workflow-scheduler-repair/canonical-smoke-0018.json`
in the CE checkout. At this checkpoint independent reviews, registration and the
outer session hook remain pending: compiled content is not reported as accepted
chapter completion. The native run continues that work.

That four-node unit subsequently completed its genuine independent source/honesty
reviews, four fidelity registrations, exact stage check, blueprint/graph refresh
and engine-owned outer hook. Its session ended at `2026-11-04T15:59:55.878252Z`
with `status: done`, `boundary.state: passed`, no scope/private violations and
`evaluation.complete: true`. The measured session span was 2,599.427 seconds
(43 minutes 19 seconds), including metadata repairs, reviews and finalization;
it is neither a chapter completion nor an end-to-end speedup factor. The retained
CE receipt is `build/workflow-scheduler-repair/canonical-acceptance-0018.json`.
The same native run then advanced automatically to the preserved DAG.3 recovery
and registered the next two-node statement unit.

## Continued-run timing and multi-author preparation (2026-11-05)

The owner authorized autonomous continuation of the whole registered book under
the existing definitions/statements scope, with formal theorem proofs deferred.
The live coordinator records read-only session-boundary timing snapshots under
`build/ce1956/metrics/`, separating accepted sessions from compiled candidates,
wall spans from overlapping phase work, and execution from observed lock waits.
Historical unavailable timings and overwritten check-receipt lower bounds remain
explicit. Source authoring, independent review and acceptance stay native-owned.

The first accepted new unit measured 250.50 seconds for four successful separate
author handoffs, 70.68 seconds for their review snapshots and 221.74 seconds for
four successful registrations. A malformed reviewer alias additionally cost
40.16 seconds before failing schema validation. These measurements motivated a
bounded follow-up in this implementation checkout:

- `workflow prepare-batch` performs one fresh full document export/validation and
  atomically publishes separate actual-author deliveries in one bundle. Explicit
  disjoint node ownership, full validation findings, input/contract rechecks and
  author selection for verification/review snapshots remain mandatory. It caches
  no result across calls and supplies no review or completion approval.
- Fidelity registration checks the existing Login schema for `--by` before costly
  input freezing/export; full identity still belongs in `--session`.
- The ordinary outer hook measures its scope, private-source, export, validation,
  document-state, stage-evaluation, planning, publication and backup calls with a
  monotonic clock. `returned` records a function return, not successful acceptance.
  Total duration includes unsegmented work but excludes final log writes; failures
  before hook-result creation still follow the original exception protocol.

Focused author/review tests had 99 passes and one invalid test setup: a YAML
replacement did not change the JSON-formatted fixture. After replacing the actual
header and asserting changed bytes, that error-retention case passed. Four
additional independent tests passed, covering changed task contracts, a private
source change after one author's recheck, fresh execution on subsequent calls,
and strict author-bound review snapshots. All 17 lifecycle tests passed with the
original operation order and failure/acceptance behavior. Independent review
found no blocking issue in these bounded changes. Combined infrastructure checks
and live installation were still pending at that focused-test checkpoint.

The companion [owner-decision replay](OWNER_DECISION_REPLAY.md) now preserves four
exact previously adopted corrections as typed agent attestations. Its actual
session-start/PR-base trust checks preserve human fields, history and the ordinary
independent review requirement. Independent review passed 27 replay cases and the
final owner-sensitive receipt-PR regression; all four live profile bindings matched
read-only. This does not adjudicate new disagreements or complete theorem proofs.

Combined infrastructure checks subsequently passed in this implementation checkout:

- `make test`: 618 Python tests passed, 17 skipped and one existing warning;
  38 site tests passed, including current generated schema types and fixture data.
- `make validate`: zero errors, eight existing warnings and 17 explicit context
  skips; all 19 actual Lean smoke/export tests passed.
- `make site`: passed, including the 145.0 KiB entry gzip and 4.4 MiB site budgets.

Logs and exit receipts are under `build/scheduling-repair/continuation-validation/`.
An initial validation correctly rejected build inputs changed during independent
review's final PR-path fix. An initial full test run exposed 42 fixture failures
because an ambient real `HORIZON_BIN` overrode the fictional worker executable;
the fixture now clears that ambient pin while explicit pinning tests set their
own. Both failed runs remain retained, followed by complete successful reruns.
The existing npm audit output reported 12 moderate advisories; dependency
lockfiles were unchanged. No production speedup is claimed from these checks.

## Repeated planning validation (2026-11-05)

The first instrumented native acceptance hook took 330.913 seconds, of which
271.776 seconds were planning. The accepted Chapter I correction session was
`0018/0007`; its scope, private-source and stage gates passed. This observation
identified repeated whole-document validation as a concrete next bottleneck.

`PlanningFacts` now reuses identical validation results and document projections
only within one read phase. Each task still receives its own stage evaluation.
Fast validation and validation against an existing full export remain separate;
failures, findings and skipped coverage are retained. Input fingerprints include
cross-document metadata, reviewed source text, task contracts, export ordering,
Git index/history and applicable native authority. Claim expiry and future-status
admission boundaries also invalidate the phase. Changed inputs abort the sweep;
no result persists across calls or authorizes acceptance. Reconciliation verifies
its read inputs before its own writes. Its pre-existing last-check/write race with
external task edits remains a limitation; operators must not mutate tasks during
that write window.

An isolated copy of actual CE inputs measured 211.151 seconds before and 33.930
seconds after the change, an 83.931% reduction for that read-only planning sweep.
All 109 complete proposals and all 30 ordered stage results matched. Findings,
skipped coverage and counts from 23 old fast validations matched the one new fast
validation, and the four old full validations matched the one new full validation.
Neither copy changed its data inputs. This excludes task writes, publication,
compilation and full-session duration; it is not a whole-book speedup estimate.
The live checkout retains `build/ce1956/metrics/planner-profile-20261105/` evidence.

The same bounded update fixes public owner-decision receipt permissions at atomic
creation: explicit mode 0644 is set before publication, while private callers keep
the default 0600. Native recovery had already corrected the four existing receipts
without changing their bytes. Worker provisioning remains serialized under the
canonical registry lock; authoring can run concurrently after each worker starts.

Independent review and complete infrastructure checks passed: 651 Python tests
and 38 site tests; validation with zero errors, eight existing warnings and 17
context skips; all 19 Lean smoke/export tests; and the site build. The initial
format-only failure is retained beside the successful rerun. Evidence is under
`build/scheduling-repair/planning-facts-validation/`. At this checkpoint installation
is prepared for a native idle boundary; live hook savings have not yet been measured.
