# Register independent review cohorts together

Several actual authors and reviewers can share one fresh document export and
one journaled registration transaction. Every node retains its own author,
reviewer, report and compiled lock. These agent-only commands require the tracked
independent-review policy. Existing single-reviewer and human commands remain
unchanged.

After a successful `workflow prepare-batch` handoff and genuine completed review
reports, write a local manifest below `build/`:

```json
{
  "schema_version": 1,
  "kind": "fidelity-review-cohorts",
  "cohorts": [
    {
      "by": "actual-reviewer-a",
      "session": "ACTUAL_REVIEWER_SESSION_A",
      "author_session": "ACTUAL_AUTHOR_SESSION_A",
      "node_ids": ["Example2000.Def_1"]
    },
    {
      "by": "actual-reviewer-b",
      "session": "ACTUAL_REVIEWER_SESSION_B",
      "author_session": "ACTUAL_AUTHOR_SESSION_B",
      "node_ids": ["Example2000.Thm_1"]
    }
  ]
}
```

Use actual sessions from the handoff and reports, never the example placeholders.
`by` is the existing short Login identifier; the full identity belongs in
`session`. Each cohort may have an optional `note`. Unknown fields are rejected.
Nodes must be unique across cohorts and belong to one task and document. For
each included author, the selected cohorts together must cover that author's
complete delivery. A ready subset of whole author deliveries is allowed; other
authors need not finish before that subset proceeds.

```sh
homalg workflow review-snapshot-cohorts build/handoff.json \
  --cohorts build/cohorts.json --out build/review-cohorts.json --json
homalg review-fidelity-cohorts --snapshot build/review-cohorts.json --json
```

The first command checks reports and freezes the exact handoff, manifest, task,
source, private context and report inputs. It grants no approval and runs no
compiler. Registration rechecks every cohort, performs one fresh document export
and writes ordinary per-node agent locks in one guarded union transaction.
Changing a file, replacing it with identical bytes, changing a task contract or
changing cohort membership invalidates the relevant snapshot. Create a new
snapshot after genuine reassessment; do not edit an existing one or reuse a
partially consumed union snapshot.

Latest source-fidelity and honesty blocks on one node must name that cohort's
actual reviewer and author, as required by the existing policy. Distinct reviewers
across nodes are supported. This API does not combine different per-kind reviewer
identities into a fictitious common reviewer, resolve open disputes, replace human
locks or grant new owner decisions. The actual reviewer may independently perform
both required reviews, retaining other reviewers' historical reports truthfully.

If registration fails, retain its transaction journal and evidence. The existing
rollback restores only the exact node versions written by that transaction;
conflicting external edits are preserved and require recovery before retrying.
Fresh generated export files are not rolled back. Successful registration is
still followed by ordinary generated-data, graph, exact stage, scope and
engine-owned session acceptance checks; it does not complete the task itself.
