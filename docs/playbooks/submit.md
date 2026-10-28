# Submit document work

Finish the current engine session and ensure the workspace has no active run.
Read [CONTRIBUTING.md](../CONTRIBUTING.md) for collaborator and claim requirements.
Submission requires an active claim held by your authenticated GitHub account
on current main. An expired claim cannot be renewed by submitting formalization.

Review the document's current state and validation findings:

```sh
homalg status --doc Hochschild1945
homalg validate --doc Hochschild1945
homalg review-summary --doc Hochschild1945
homalg submit Hochschild1945
```

The command checks idleness, snapshots work through the engine integration,
creates an isolated temporary worktree from current main and builds a
`formalize/<DocKey>-N` PR. It copies the permitted document paths, merges taxonomy
additions by stable id, regenerates roots and authored data, exports Lean facts
and validates the result. It checks ownership and expiry again after the build.
The user's current branch and unrelated staged changes are preserved.

The submission integration archives this document's local inbox entries and
node comments under `run-log/`, and publishes numeric status. Raw agent logs,
page transcriptions, PDFs and page images remain private. Missing integration
fails submission; it does not silently omit these steps.

Use `homalg submit Hochschild1945 --release-claim` at the end of the claim.
Unresolved issues eligible for GitHub escalation are presented for explicit
confirmation through the engine integration. During the run use the local inbox;
do not create GitHub issues directly. A staged submission without this option
keeps the claim active. `--no-claim` is reserved for synthetic maintainer documents.

Inspect the proposed PR before merge. Its description should state the completed
scope, new nodes, status changes, deviations, remaining named `sorry` declarations,
validation and any unresolved source questions. The user override dated 2026-10-28
allows properly recorded independent-agent foundation, first-chapter and explained-
deviation reviews; describe them as agent reviews. Unresolved disputes retain
their human decision gate. Sensitive metadata needs owner
approval on the newest head SHA. Existing taxonomy entries and relation reviews
are outside an ordinary document submission's append-only scope.

After the PR merges, stop before discarding local work. Update the local checkout
without losing unrelated changes, rerun `homalg plan` for the next eligible stage,
and retain the engine/private backups described in [ENGINE.md](../ENGINE.md).
