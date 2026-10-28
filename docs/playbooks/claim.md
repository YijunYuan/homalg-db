# Claim and start a document

Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [ENGINE.md](../ENGINE.md).
Use your own authenticated GitHub account with collaborator access. Register an
unknown document with `homalg new-doc` before claiming it. Registration publishes
only public metadata and an empty claim; the PDF stays in the private library.

```sh
homalg claim Hochschild1945 --chapters 1,2 --days 90 --note 'Initial chapters' --dry-run
homalg claim Hochschild1945 --chapters 1,2 --days 90 --note 'Initial chapters'
```

The dry run reads current remote state without publishing. The second command
creates the claim PR, enables auto-merge and waits. `--no-wait` returns after
auto-merge is enabled. Start formalization only after the claim has merged and
your checkout contains it. Claim operations use temporary worktrees; they preserve
the current branch and unrelated staged changes.

The default term is 90 days. Valid publications on `status/<DocKey>` extend an
unbroken active claim by 14 days. Activity after expiry cannot revive it. An
expired claim can be taken using the same `claim` command; a live claim held by
another contributor cannot. The initial policy allows two active plus pending
claims. Use `homalg renew Hochschild1945 --days 30` for an explicit renewal and
`homalg release Hochschild1945` to relinquish the work.

After the claim is available locally:

```sh
make literature
homalg ingest-pdf Hochschild1945
homalg horizon-init --engine codex
homalg doctor
homalg plan Hochschild1945 --chapters 1,2
horizon run '*' --rounds 1
```

Configure the private repository URL locally; never put it in committed files.
`horizon-init` installs the pinned fork's resources and configures its hooks.
The default permits one run in a workspace. Tasks appear only when their
prerequisites are ready. Rerun `homalg plan` as work progresses; it preserves
existing tasks. The user override dated 2026-10-28 permits independent agents to
complete the first-chapter checkpoint and foundation/fidelity reviews through the
commands in [review-fidelity.md](review-fidelity.md), with distinct author/reviewer
sessions and the enabled repository policy. Unresolved disputes still require a
human decision. Never invoke human-only guards or manually write protected fields.

Read each task's objective and explicit write scope. Work on the local work branch
and commit formalization progress only to `hgit`, the engine ledger. Publish with
[submit.md](submit.md) after the engine is idle.
