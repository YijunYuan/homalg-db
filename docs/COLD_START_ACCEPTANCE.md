# Cold-start acceptance

This report records the live 2026-10-28 rehearsal in the separate public
[acceptance repository](https://github.com/YijunYuan/homalg-db-acceptance).
Fixture2002 is project-authored synthetic arithmetic, not a literature result.
Its nodes, review records and proofs must not be copied into the production
golden fixtures.

**M4-T4 passed:** both real CLI engines completed STMT and PROOF tasks; the actual
submission PR passed CI, merged normally, and its deployed page shows two proved
nodes. **M4-T5 passed for both live production status snapshots:** the
published branch payloads and visible claims-page numbers matched exactly,
including the final stable snapshot with no remaining owner questions.
The formal pilot submission, repair deployment and strengthened live browser
acceptance also passed; their separate evidence is recorded below.

## Environment and source boundary

The executable was installed from the published
[v0.1.5-homalg.1 wheel](https://github.com/YijunYuan/homalg-horizon/releases/tag/v0.1.5-homalg.1),
whose SHA-256 was
`a3ed66cffd7ec740b814e19956272a08fbb60543a39668fb151eb5781c1eb13c`.
The reported engine version was `0.1.5+homalg.1`; Claude Code was `2.1.305`
and Codex CLI was `0.164.0`. Both used their configured defaults, without a
model or reasoning override. No API usage charge or exact provider model is
inferred from the interactive subscription sessions.

Claude and Codex ran in separate fresh clones. Each clone had its own Lean
build directory and Python environment. The pinned Mathlib package cache was
reused as a dependency-cache optimization; this was not an empty-cache
download benchmark. The private-reference repository was empty. The only source
for this exercise was the public, paginated `docs/fixtures/Fixture2002.md`.
Both source headers initially had empty `decls`. No mathematical implementation
was supplied outside the repository instructions and that source.

Before submission, the empty private repository received a synthetic README and
a local ignored bare origin so the real backup hook has an actual destination.
This verifies local private Git backup behavior, not GitHub private-repository
hosting. It does not contain or copy the production private literature.

The two source statements are `n + 0 = n` and `n * 1 = n` over the natural
numbers. The second source proof explicitly expands multiplication recursion,
zero multiplication and zero addition. The independently confirmed foundation
boundary names those elementary operations and equations. Preparation used the
normal inventory, DAG, foundation review and early-review commands; the actual
author and independent reviewer sessions are retained in the test repository.

## Executed tasks

Each command used the installed release engine:

```sh
horizon run Fixture2002.STMT.3 --rounds 1 --no-dashboard # Claude clone
horizon run Fixture2002.PROOF.1 --rounds 1 --no-dashboard
horizon run Fixture2002.STMT.4 --rounds 1 --no-dashboard # Codex clone
horizon run Fixture2002.PROOF.2 --rounds 1 --no-dashboard
```

| Engine | Task | Actual session | Result |
| --- | --- | --- | --- |
| Claude Code | STMT.3 | run 0001 / 0002-horizon-Fixture2002.STMT.3 | Done; exact statement, separate named `sorry`, actual independent source review and lock |
| Codex | STMT.4 | run 0001 / 0002-horizon-Fixture2002.STMT.4 | Done; exact statement, separate named `sorry`, actual independent source review and lock |
| Claude Code | PROOF.1 | run 0002 / 0002-horizon-Fixture2002.PROOF.1 | Done; `rfl` follows the defining addition equation; independent honesty review satisfactory; axioms empty; stage and session scope checks passed |
| Codex | PROOF.2 | run 0002 / 0002-horizon-Fixture2002.PROOF.2 | Done; `Nat.mul_succ`, `Nat.mul_zero`, `Nat.zero_add` in the source order; independent honesty review satisfactory; transitive axioms empty; scope-check passed |

Claude STMT ran from 04:51:03 to 05:22:08 UTC. Codex STMT ran from 05:06:56
to 05:18:00 UTC and PROOF from 05:23:42 to 05:34:55 UTC. Claude PROOF ran
from 05:24:00 to 05:45:32 UTC. These are observed
end-to-end session times, including tool and reviewer waits. Horizon ledger
commits are session evidence; they are distinct from the user's ordinary Git
branch commits.

## Defects exposed by the live runs

- A document-only Lean export printed `Nat`, while the whole-library export
  printed `ℕ`. Semantic hashes agreed, but generated text freshness failed.
  The exporter now uses the pinned builtin printer and fully qualified type
  notation. A real Lean regression covers unrelated notation, custom printers,
  root ordering and actual type changes. The 25 baseline declarations retain
  every other raw field. Freshness checks have not been weakened.
- Tests selected every `Fixture*` document while loading a golden export for
  only Fixture2000/2001. The fixed baseline corpus is now explicit, with a
  regression proving that extra documents are excluded while errors in a known
  baseline document still fail validation.
- A temporary test directory beneath a Horizon checkout let Git discover the
  ancestor's `origin/main`. The maintenance test now initializes its own empty
  repository before checking the missing-baseline case.
- Blueprint markup interpreted the spaced multiplication signs in
  `n * 1 = n * 0 + n` as emphasis. The renderer now preserves that equation,
  protects inline code and tests genuine emphasis separately.
- PR classification treated every `Fixture` prefix as infrastructure. Only the
  two fixed baseline documents are exempt now; Fixture2002 is a formalization.
  The synthetic-only `--no-claim` restriction remains in force, including a
  regression for a real article whose key happens to begin with `Fixture`.
- Submission previously ran the private backup before snapshotting dirty source
  files from the Horizon ledger into ordinary Git. It now snapshots scoped
  source first. Real local Git regressions verify that the private destination
  contains that source and that backup failure prevents public push and PR
  creation; claim and idle checks still run first.
- Claude's first statement run encountered two Lean LSP initialization timeouts
  and a bounded polling mistake after the reviewer had already recorded its
  lock. The session recovered using the serialized build/export commands.

The original Codex reports honestly retain the failing whole-repository checks
from their original baseline. Repairs and subsequent successful reruns are
separate evidence, rather than edits to those historical reports.
The repaired Codex clone passed all 363 Python tests (16 contextual skips) and
all 31 frontend tests. Two external-prerender integration cases exposed a
15-second harness timeout under concurrent work; they now terminate the child
after 45 seconds and have a 60-second outer deadline. Their substantive
assertions, 1-millisecond injected layout failure and product performance budgets
are unchanged. The complete frontend rerun took 7.27 seconds.
After canonical export regeneration, fixture freshness, 31 frontend tests and
18 browser tests passed. The production build remained within its budgets:
144.1 KiB entry JavaScript gzip and 4.3 MiB complete site.
An initial fully expanded printer was rejected after the pilot exposed
multi-megabyte signatures. The final deterministic printer hides implicit
instances and proof terms; the reported browser/build results were repeated
against that compact version (18 browser tests in 22.0 seconds).
The pilot's 346 declaration types total approximately 258 KB, with the largest
approximately 8.7 KB. The final exporter/Lean smoke run passed all 19 tests.

## Remote acceptance boundary

The initial synthetic-only setup was merged as
[PR #10](https://github.com/YijunYuan/homalg-db-acceptance/pull/10).
It removed an inherited active research registration; the resulting claim and
scope guards rejected that administrative cleanup. An explicit administrator
bypass was used for this setup only. Infrastructure
[repair PR #12](https://github.com/YijunYuan/homalg-db-acceptance/pull/12)
subsequently passed every applicable check, including Lean, and was merged by
ordinary squash merge as `29895d16b562a30d673699340f6738f70e99a0da`.
The actual `homalg submit Fixture2002 --no-claim` command then succeeded and
created [PR #13](https://github.com/YijunYuan/homalg-db-acceptance/pull/13).
Its [final CI run](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40642480584)
passed classify, checks, Lean and gate; owner-approval also passed. GitHub
reported `mergeStateStatus=CLEAN` and no review requests. The PR was merged by
ordinary squash merge without administrator/force options or rule changes. Its private backup was
inspected and contains the current source proof. The merge commit is
`4e96a3939cb0f6c39bd841b485ede6eec9f18745`.

The first Pages deployment encountered a Lean download TLS failure. Retrying
the failed jobs produced a successful
[deployment](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40635014052).
The [final deployment](https://github.com/YijunYuan/homalg-db-acceptance/actions/runs/40643719471)
passed. A real browser read the matching manifest commit, opened the document,
and checked the claims card's visible text, `2 of 2 items proof complete`.
The manifest reports `proved=2`, `planned=0`, and `proof-complete=2`, with zero
JavaScript errors and zero failed responses. This also verifies relative asset
paths on the actual repository Pages URL. Evidence and screenshots are in
`build/acceptance-deployed-final.json`, `build/acceptance-deployed-final-claims.png`
and `build/acceptance-deployed-final-document.png`. The test repository has no
open PRs after this acceptance merge.

The first Lean setup attempt on PR #12 and the first PR #13 attempt encountered
the same upstream TLS download failure. The deployment after PR #12 also failed
at setup, so PR #13's main-health check correctly stopped it while main was red.
The deployment then passed on a normal retry; submission checks were retried
only after main was green. The health brake was not disabled and no `repair`
label was used to evade it.

No user review requests were sent. Development Dependabot update PRs were
closed without comments and automatic version-update PRs were disabled in the
test repository. No real two-account GitHub claim race or non-owner merge-denial
exercise was performed. Local dual-actor tests and the live active ruleset
(`require_code_owner_review=true`) provide narrower evidence. A successful
`owner-approval` check on an ordinary dependency update does not demonstrate
non-owner rejection: that check handles sensitive fields, while CODEOWNERS
protects infrastructure paths.

## Production status publication

The numeric status rehearsal used the existing real Hochschild1945 claim in the
production repository. This deliberately differs from the original test-repo
location: no extra claim PR or review notification was created for the exercise.
The normal `homalg publish-status Hochschild1945 --force --json` command
published `status/Hochschild1945` at
`e268134aff210abf306872cd2b2bf45e0f4dac51`, with status time
`2026-10-28T06:37:20Z`. The actual remote branch was fetched again and its JSON
retained as the expected payload.

Production [deployment 40645173934](https://github.com/YijunYuan/homalg-db/actions/runs/40645173934)
completed successfully from main commit
`34ca001157dcccb99eb5878aac4e77be500af79e`. At 06:43:58 UTC the real browser
read that exact deployed manifest and compared the complete status counts,
holder and generation time with the branch payload. The visible claims card
read `26 proof complete · 10 pages reviewed · 1 questions for a human`, beneath
the explicit “In progress, not validated by CI” notice. The browser's Shanghai
time display of 2:37:20 PM corresponds to the published UTC timestamp. No
JavaScript errors occurred. The verification used actual network responses;
it did not intercept requests or replace the deployed data.

This is historical status-flow evidence, not the final mathematical tally.
The first snapshot had 29 source items: 26 proof complete, one in progress,
one statement complete and one confirmed error. A subsequent freshness audit
and independent review completion required another stable snapshot. The one
owner question shown in this capture was subsequently closed through the
normal inbox command after the actual owner decision; the confirmed source
error itself remains recorded. Neither the historical JSON nor screenshot was
rewritten to show later counts.

The original publication output, refetched payload and live verification are
retained at `build/acceptance-live-status-publish.json`,
`build/acceptance-live-status-expected.json`, and
`build/acceptance-live-status-first-capture.json` with its PNG screenshot.
The reproducible checker is `site/scripts/verify-live-status.mjs`.

After the final source checks and normal completion of every stage, a second
publication produced status commit
`ad2ad1ad711004943066ece77332d7ad21de9544` at `2026-10-28T09:35:00Z`.
The refetched remote branch matched the command's entire returned status.
Production [deployment 40665487067](https://github.com/YijunYuan/homalg-db/actions/runs/40665487067)
then passed. At 09:39:34 UTC, the strengthened browser checker compared the
whole deployed status object, including the last green check and stage totals,
and confirmed the visible text
`27 proof complete · 10 pages reviewed · 0 questions for a human`.
All 29 source items are accounted for: 27 proof complete, one statement complete
and one confirmed error. PROOF is 6/6 and STMT is 12/12; all other planned
stages are also complete. The last check is green at `2026-10-28T06:57:38Z`.
There were zero JavaScript errors, zero HTTP failures and zero failed requests.
The JSON, log and visually inspected PNG are retained under
`build/acceptance-live-status-final-capture.*`; publication and refetched
payload evidence use the corresponding `final-publish` and `final-expected`
names.

Both status deployments used the existing main registration at commit
`34ca001157dcccb99eb5878aac4e77be500af79e`. Its public formalization count was
still zero, while the clearly labelled in-progress notice showed the real
unmerged run. This is the intended separation between published progress and
CI-validated source data. The actual pilot's merged document, proof details
and search are separately verified below.

## Real pilot session before submission

The production pilot also completed an actual release-engine session:
run `0001`, session `0002-horizon-Hochschild1945.PROOF.1`, using the configured
Codex subscription harness. Its metadata records a start at
`2026-10-28T06:48:27.304399+00:00` and completion at
`2026-10-28T06:56:48.296101+00:00`. Model, reasoning effort and monetary cost
were not reported; no exact value is inferred for them.

This was a final verification of six already implemented chapter-1 nodes,
not a claim that a cold-start session authored the whole pilot. The agent used
an independent honesty reviewer, preserved the locked statements and proofs,
and ran the stage, scope, Lean, test, validation and site-build checks. The
session report explicitly says that browser and deployment checks were not run
and that chapters 2–6 remained separate tasks at that time.

The actual `after-session` hook subsequently returned zero, marked the task
done, found no private-scope violations, and recorded a successful backup.
Its automatic status publication was throttled; it did not claim to publish a
new status snapshot. Chapters 2–6 were then checked and completed through
their normal separate stage commands. The run metadata and original report
remain under `.archon-horizon/runs/0001/sessions/0002-horizon-Hochschild1945.PROOF.1/`;
copies of the report, hook result and verification logs are retained under
ignored `build/pilot-engine-*`. This session and its hook provide actual
production workflow evidence before the separately checked PR and deployment.

## Formal pilot submission

The actual `homalg submit Hochschild1945` command returned success with no
errors or warnings and created production
[PR #16](https://github.com/YijunYuan/homalg-db/pull/16) at 09:43:44 UTC.
The source branch is `formalize/Hochschild1945-1`, with head
`e4b0cd6c8bc7b85e6a02903292d003855cfbcf85`. Unlike the synthetic acceptance
submission, this used the existing real claim. The normal submission rebuilt
and validated the scoped document in an isolated worktree and backed up its
committed source before publication. No user review request was created.

The command result is retained in `build/pilot-submit.json`, and the actual
GitHub PR metadata in `build/acceptance-live-pilot-pr16.json`. The local full
data/site build also passed: 61 nodes across three documents, 201 edges,
144.1 KiB entry JavaScript gzip and 9.1 MiB total site. Those local results
do not substitute for PR CI or deployed-page acceptance.

The actual [PR validation run](https://github.com/YijunYuan/homalg-db/actions/runs/40666512164)
passed every applicable check, including Lean in 3 minutes 43 seconds. The PR
was merged through the standard REST squash endpoint at `2026-10-28T09:52:25Z`,
using the exact expected head SHA. No administrator/force option, rule change
or review request was used. The resulting main commit is
`5b4771d924974ea59a9c4c1ec5bd5713af4e6482`; the independently retrieved
merged PR metadata is retained in `build/acceptance-live-pilot-pr16-merged.json`.
Its push started [production deployment 40667644896](https://github.com/YijunYuan/homalg-db/actions/runs/40667644896),
which completed successfully. Real public-data and browser checks against the
exact merge commit passed: 29 source items, 27 proof-complete headlines, one
dependency-limited corollary and one confirmed source error; all 12 source
items in sections 1–3 and all three bridges have no local or transitive sorry.
Theorem 4.1 has a complete local proof with its classical citation boundaries,
and the owner decision, source-error report and final theorem review are
available at the same public commit. Search for `Thm_4_1` opened the correct
detail, proof and dependencies. No JavaScript, HTTP or request failures occurred.

Visual inspection found a separate product issue: the expanded 44-node graph
could extend beyond the canvas because the minimum zoom was chosen from node
count, even for a long sparse layout. A two-node browser regression with a
20,000-unit span reproduced the clipping; its upper edge lay 889.51 pixels
outside the viewport. The fix uses the existing smaller zoom limit for every
document. All 19 browser tests and 31 frontend unit tests then passed, along
with type checking, lint and bundle budgets. Independent reviewers inspected
the change. The initial data/interactivity success is not presented as proof
that this display issue was absent; the repair has separate deployed evidence.

The fidelity-view explanations were also checked separately after screenshots
captured some asynchronous content too early. All six actual node requests
returned 200 and their explanations rendered completely. No product data fix
was needed. The final browser checker now waits explicitly for every deviation's
explanation and verifies the settled graph's actual rendered bounds. Initial
capture evidence is retained under `build/acceptance-live-pilot*`; the failed
and passing graph regression logs use `build/acceptance-graph-fit-*`.

## Final repaired deployment acceptance

[Repair PR #17](https://github.com/YijunYuan/homalg-db/pull/17) passed its
[applicable CI checks](https://github.com/YijunYuan/homalg-db/actions/runs/40670365185)
and owner-approval check. Lean was correctly skipped for this infrastructure
PR because `needs_lean=false`; the deployment still built and validated the
complete source library. The PR was merged at `2026-10-28T10:16:06Z` through
the standard GitHub REST squash endpoint with the exact expected head SHA,
without administrator/force options or rule changes. The CLI's prior
`BLOCKED` precheck did not explain its cause, so no synchronization explanation
is inferred from it. The resulting commit is
`c5489f42b97470d6424778a0b8134ed59c520d0a`.

[Production deployment 40670763457](https://github.com/YijunYuan/homalg-db/actions/runs/40670763457)
passed. The actual public-site acceptance completed at
`2026-10-28T10:21:00.933Z`, requiring that exact manifest commit. All 17
assertions passed, using real public fetches and Chromium without request
interception. The settled expanded Blueprint contains all 44 pilot nodes,
including auxiliaries and citations. Its measured bounds are
`x=573.33..661.67, y=35..605` inside a `1235 × 640` canvas, with no clipping.
The complete overview, a readable first-chapter view, the list and the
fully loaded Fidelity page were captured and visually checked.

The deployed data and visible pages retain the mathematical boundaries:

- All 29 original source items appear in the list. Headlines are 27 proof
  complete, one statement complete and one confirmed error.
- The 12 source items in sections 1–3 and the three explicit Mathlib bridges
  have complete local proofs, no transitive sorry and only standard axioms.
- Theorem 4.1 has no local sorry and displays its identified classical
  citations as `proved-modulo-citations`; no citation-free proof is claimed.
- Theorem 5.1 displays the actual owner-confirmed source error and preserved
  unproved original assertion. Its review and owner-decision reports are
  accessible at the same immutable commit.
- The quotient-separability corollary is locally proved, while its
  `statement-complete` headline conservatively retains the source dependency
  on Theorem 5.1 and the explained replacement proof route.
- Every recorded deviation's explanation loaded in the Fidelity view. Exact
  local-identifier search for `Thm_4_1` found the expected result and opened
  its complete Lean source and citation details.

There were zero JavaScript errors, zero HTTP failures and zero failed requests.
The final report and log are `build/acceptance-live-pilot-final.json` and
`build/acceptance-live-pilot-final.log`; eight stable screenshots use the
`build/acceptance-live-pilot-final-*.png` prefix. The actual checker is retained
as `build/verify-live-pilot.mjs`. The earlier reports and screenshots remain
available separately, including the pre-repair visual evidence.

## Retained evidence

Complete transcripts, session metadata and original reports are retained locally
under ignored `build/cold-start-acceptance/`; they are not public data artifacts.
The exact fixture sources and review reports live in the acceptance repository.
Repair checks include 64 fixture/isolation tests, 12 engine/render tests,
27 classification/collaboration tests and the additional article/no-claim
regression. The repaired-clone and merged infrastructure PR results are above;
the final synthetic submission, its published two-proof view, both production
status snapshots, the formal pilot submission and the final repaired
production browser acceptance all passed with their own retained evidence.
