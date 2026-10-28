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
