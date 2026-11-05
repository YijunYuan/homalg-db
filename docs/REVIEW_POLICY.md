# Independent review policy

On 2026-10-28 the owner explicitly approved replacing mandatory human review of
first-chapter definitions, foundations and explained formalization deviations
with independent agent cross-review and automatic continuation. Unresolved
mathematical or source disagreements are escalated. This supersedes the relevant
human-only requirements in version 1.0 without relabelling agent judgments as human.

The tracked `horizon/review-policy.yaml` enables this mode. Missing or false policy
retains the original behavior. Formalization sessions cannot edit the policy;
scope checks read its start-of-session ledger version. PR checks read the trusted
base version, so a contribution cannot enable its own exemption.

## Required evidence

- Author and reviewer are distinct sessions, recorded as `author_session` and
  `session`. The actual independent reviewer inspects the source and Lean claim.
  Reports include satisfactory source-fidelity verdicts and comparison tables;
  required honesty reviews remain mandatory.
- A foundation's agent confirmation includes a SHA-256 of its content, including
  notion, Mathlib names, evidence and justification. Edits invalidate it.
  `confirmed_by` remains human-only; agents use `confirmation.kind: agent`.
- Fidelity locks retain agent provenance and compiled hashes. Changed statements
  or dependency meanings reopen their reviews through the existing checks.
- The early-review gate accepts independently reviewed first definitions and
  current foundation confirmations. Newly proposed or stale foundations block
  advancement again.
- Genuine human records cannot be replaced or removed by an agent session.
  Optional human commands retain their interactive-terminal and inactivity guards.

Session names are an audit trail, not cryptographic proof of independent execution.
The orchestrator must actually delegate review; inventing a reviewer identity or
copying an author's own verdict is not compliant.

Parallel authorship and batch registration do not change this requirement. Every
node needs complete current source-fidelity evidence and any required honesty
review. A coordinating operator preserves the identities of the actual author
and reviewer; the operator's execution is not a substitute review. Freeze and
recheck the reviewed source, node and dependency inputs at the integration
boundary. Changed inputs must be assessed and reviewed again where required.
Compilation and hash validation can be shared operational work, but neither
supplies an independent verdict. See [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md).

Evolution summaries may also carry explicit independent-agent provenance under
this policy, after checking their current source bundle and claims. This does not
replace protected-path GitHub ownership or taxonomy-maintenance approval rules.

## Agent commands

The foundation report is `literature/KEY/reviews/foundations.md` and names every
notion being approved. Node reports are `reviews/LocalId.md`. Include `Session:`
and `Author-session:` lines matching the actual sessions and command arguments.

```sh
homalg foundations review KEY 1 --by REVIEWER --session REVIEW_SESSION --author-session AUTHOR_SESSION
homalg review-fidelity KEY.LocalId --by REVIEWER --session REVIEW_SESSION --author-session AUTHOR_SESSION
```

`review-fidelity-snapshot` and `review-fidelity-batch` support coordinated
registration of multiple independently reviewed nodes in one document with the
same actual provenance. They retain per-node evidence and do not permit human
impersonation or replace substantive review. The snapshot command grants no
approval; the batch command always builds fresh compiled facts. See
[the batch and recovery contract](PARALLEL_WORKFLOW.md#registering-reviewed-nodes-together).

After the usual claim and stage prerequisites are satisfied:

```sh
homalg plan KEY --early-review-ok --by REVIEWER --session REVIEW_SESSION --author-session AUTHOR_SESSION
```

Source fidelity, assumptions and proof-route requirements are unchanged. Record
unresolved contradictions, source ambiguities and genuine source-error disputes
for the owner instead of manufacturing satisfactory verdicts. This policy does
not authorize automatic human dispute resolution or arbitrary external messages.

Previously adopted, exactly bound owner directions can be registered using the
separate [owner-decision replay protocol](OWNER_DECISION_REPLAY.md). Its typed agent
relay is not a human confirmation and does not satisfy independent review gates.

A separately typed, prospectively enabled route may adjudicate a uniquely local
proof-membership typo after two actual independent source/data-impact reviews.
See [Routine agent proof errata](AGENT_PROOF_ERRATA.md). This grants no human or
owner attribution, ordinary fidelity lock, task acceptance or proof completion.
Substantive argument changes and ambiguous corrections remain outside that route.
