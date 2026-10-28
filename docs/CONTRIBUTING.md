# Contributing

HomAlgDB formalizes what each document says, including its proof route. Read
`CONVENTIONS.md` before editing nodes. A document has its own namespace, flat node
directory, metadata and claim. Contributors use their own authenticated `gh`
account and must have collaborator access; fork PRs are not supported.

## Set up a clone

Install the pinned Lean toolchain, Python 3.12+, uv, Node.js 22+ and GitHub CLI.
Run the README's quick start, authenticate with `gh auth login`, and install the
local hook with `git config core.hooksPath .githooks`. Keep work on a named `work`
branch based on `origin/main`; this branch is backed up privately, not published
as an intermediate formalization branch.

The public repository never contains PDFs, rendered pages or private
transcriptions. Set `HOMALG_LITERATURE_REPO` to the private literature repository
and run `make literature`. The URL belongs in your local environment or ignored
configuration, never in committed files. New documents start with a registration
PR containing only `document.yaml` and an empty `claim.yaml`; their identity and
foundations require owner review.

## Claim a document

```sh
homalg claim Example2000 --chapters 1,2 --days 90 --note 'Initial chapters'
homalg renew Example2000 --days 30
homalg release Example2000
```

The command refreshes `origin/main` and the document's status branch separately,
checks current ownership and active/pending claim limits, then creates a PR from
an isolated temporary worktree. It enables squash auto-merge and normally waits
for checks and merge. `--no-wait` returns after enabling auto-merge; `--dry-run`
previews the transition using remote read operations without creating a branch
or PR. Your current branch and staged unrelated files are preserved.

A claim defaults to 90 days. Valid status publications extend an unbroken active
claim by 14 days. Wrong-holder, malformed, pre-claim and excessively future
publications are ignored. Publications after expiry cannot revive a claim.
Other contributors may take over only after effective expiry. At most two active
plus pending claims are permitted by the initial policy. Synthetic documents are
maintainer fixtures and use no claim.

## Formalize and submit

Within a configured Horizon workspace, use `homalg plan` and the generated stage
tasks. Record unresolved source errors and questions in the local inbox. Human
foundation confirmations, fidelity reviews and dispute resolutions must use their
guarded commands. Never manufacture those fields in an agent session.

```sh
homalg submit Example2000
homalg submit Example2000 --release-claim
```

Submission requires an idle engine and an active claim on current main. It makes
a scoped work snapshot, constructs `formalize/Example2000-N` in a temporary
worktree, copies only that document's files, merges taxonomy additions by stable
id, regenerates roots and metadata, and runs the Lean export and validation.
Unrelated staged work remains outside the submission. Claim state is restored
from main and checked again after the build; an expired claim cannot be renewed
by a formalization PR. Claim release exports and escalates unresolved issues only
through the engine's submission integration. Missing integration is an error,
not permission to skip those steps. Maintainers can submit a synthetic document
using `--no-claim`.

Taxonomy additions preserve existing records. Conflicting additions with the same
id stop submission. Changes to existing vocabulary require the
`taxonomy-maintenance` label and owner approval. Node ids are permanent; do not
rename a merged node or edit another document to add an import.

## Pull-request review

Titles include a task identifier for infrastructure work. Descriptions use four
sections: Summary, FR-NFR covered, How verified, and Not done & spec issues.
Formalization summaries list new nodes, state changes, deviations, and every
remaining named `sorry`.

The two required checks are `gate` and `owner-approval`. CODEOWNERS protects
infrastructure, tooling, schemas, the site and relation reviews. Document identity,
year, type, foundations and import exceptions are checked by field; ordinary page
range edits need no owner approval. A new push invalidates the previous owner
approval. The repository owner may approve their own sensitive changes through
the explicit policy exception, and administrator bypass is limited to pull
requests in the personal-repository ruleset.

Run `make test`, `make validate` and `make site` before publishing infrastructure
work. The available CLI commands are listed by `homalg --help`; repository setup
and live workflow acceptance are described in `CI.md`.
