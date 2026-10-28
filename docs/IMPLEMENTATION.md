# Implementation and acceptance

This checkout implements the approved HomAlgDB requirements version 1.0
(2026-10-27). The table separates delivered local functionality from acceptance
that still needs mathematical work or a remote deployment. The owner's
[2026-10-28 amendment](REVIEW_POLICY.md) replaces routine human review gates with
independent agent reviews; only unresolved mathematical/source disagreements are
escalated.
It must not be read as a claim that M0–M7 are all accepted.

| Milestone | Local implementation | Remaining acceptance |
| --- | --- | --- |
| M0 | Repository layout, pinned Lean/Mathlib, licenses, two original paginated fixtures, 17 nodes, schemas, taxonomy, CLI, CI/governance configuration | Public repository/CI/deployment and human vocabulary review |
| M1 | Header lexer, document/claim models, authored extraction, compiled JSON exporter, global index, static artifacts, semantic checks, authoring/review/taxonomy helpers, conventions | Actual remote PR contexts and human review of the real pilot |
| M2 | React blueprint, source/Lean node view, fidelity audit, search, claims, source adapters, workers, accessible controls and content-addressed loading; browser timing targets passed | Deployed site |
| M3 | Claim/renew/release/submit, typed PR classification, current-main ownership, owner approval, append-only rules, incremental CI and rulesets | Apply settings and exercise actual GitHub PRs/approvals/status branches |
| M4 | Fork patches P0–P10, adapted skills, wheel with dashboard, hooks, planning/stages/scopes, private snapshots, progress/backup/sync/escalation, task templates/playbooks | Published release installation and cold-start Codex/Claude tasks producing a green remote PR |
| M5 | Exact supplied PDF identity; all 10 body pages visually transcribed and independently reviewed; 29-item inventory; 11 agent-confirmed foundations; first definitions locked; §1–§3 proofs and three bridges compiled | Complete later statements and independent locks, early-review workflow and deployed pilot |
| M6 | Concepts/relations, global graph/timeline, bundle/run/import/status/review, provider adapter, cumulative cost bound, stale summaries, hallucination checks, real two-source rehearsal | Designated human summary review; separately paid API execution is not claimed |
| M7 | SQLite/FTS5 API, static/API parity, 100k benchmark, search partitions, graph overview strategy, session ledger concurrency, migration framework, security/runner documentation; browser timing targets passed | Optional doc-gen4 measured only after pilot completion |

All advertised CLI commands are implemented; `homalg --help` is the current
command inventory. Unavailable context is listed in `summary.skipped`. A fast
validation run does not claim Lean, private-source or remote PR coverage that it
did not have. Human-only commands never fabricate approvals.

## Verification evidence

Local checks on 2026-10-28:

- `make test`: 333 Python tests passed, 14 skipped; Ruff, generated TypeScript,
  frontend lint/format and 28 frontend unit tests passed. The skipped checks are
  actual Lean-dependent tests and the opt-in large benchmark, run separately.
  Site fixture artifacts regenerated from the committed raw-export golden match.
- Browser suite: 15 tests passed, including static navigation/accessibility,
  evolution rendering, actual SQLite API search/node/timeline/concepts, and
  chapter-scoped requests for a large document.
- Lifecycle/API focused suite: 46 tests passed. Temporary local Git remotes
  verify ownership, expiry, publication races, no force pushes, private snapshot
  recovery, idempotent attempts, three-stall blocking, scoped backups and sync.
- Fork suite: 503 tests passed at the implementation handoff, with additional
  recovery and concurrency regressions passing afterward. Its dashboard unit and
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

The most recent complete top-level acceptance run must be repeated after the
pilot finishes changing Lean source. Use:

```sh
make test
make validate
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
11 foundation entries have independent agent confirmations under the approved
policy. Each record includes the author/reviewer sessions and a content hash;
no human confirmation was invented.

No public GitHub repository, PR, release or Pages deployment had been created at
this checkpoint. Read-only GitHub checks found neither `YijunYuan/homalg-db` nor
`YijunYuan/homalg-horizon`. The private literature source exists and is accessible.
No paid provider call has been made by the evolution implementation tests.

The real evolution rehearsal uses the 1945 pilot and verified primary-source
pages from Hochschild's 1942 paper. The current interactive agent generated the
summary; its exact model identifier was unavailable and is recorded as
`not-reported`. No provider usage/cost is invented. The importer writes an
unreviewed version in an isolated rehearsal repository because the second paper
is not yet inventoried in the live database. Evidence, output and reproduction
instructions are in [docs/evolution](evolution/README.md).

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
15. **Optional doc-gen4.** It is not enabled or claimed within its cost gates
    without a post-pilot measurement. Its optional status does not waive the
    required core pipeline, site or mathematical acceptance.

## Provenance of contributor-authored support nodes

The requirements' `statement-provenance` exemption list did not mention auxiliary
and bridge nodes, although M5 requires new comparison theorems absent from the
historical paper. The implementation therefore restricts verbatim paragraph
comparison to source-item statements and skips nodes with `aux` metadata,
including bridges. Their parent, source anchors, dependency and compiled-witness
checks still apply. Verbatim cited statements remain checked; only explicitly
editorial citations have the existing citation exemption. A regression exercises
all four cases against reviewed private page hashes.
