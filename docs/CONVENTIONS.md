# Formalization conventions

These conventions implement the approved requirements version 1.0. Read them
with [ARCHITECTURE.md](ARCHITECTURE.md), [ENGINE.md](ENGINE.md), and the focused
[playbooks](playbooks/write-node.md). The original specification and the owner's
[2026-10-28 review amendment](REVIEW_POLICY.md) remain normative where a translated
explanation is incomplete.

## Fidelity

P-1: reproduce the source's definitions, assumptions, generality and construction.
An equivalent Mathlib concept is a recorded counterpart, not a replacement.
P-2: follow the source's proof dependencies. A shorter proof that bypasses a cited
document lemma does not reproduce the document's route.

Each document declares its own foundation boundary. Template entries are merely
draft suggestions. Under the enabled review policy, an independent agent checks
source evidence and confirms each entry through the agent review command. The
confirmation binds all entry content and actual session identities. Optional human
review remains available; an agent cannot grant a human approval. A nonunital
algebra must not inherit the template's unital-ring assumption. Later additions
reopen the foundation gate; supply a quotation/location and justification before
proposing each entry and remove irrelevant suggestions.

## Nodes

`DocKey` follows `[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*`; its year matches the document
record. `LocalId` follows `[A-Z][A-Za-z0-9]*(_[A-Za-z0-9]+)*`. A node's path, module,
header id and document must agree. Source declarations use `namespace <DocKey>`.

Use kind prefixes to distinguish identical numbers, such as `Lem_4_1` and
`Thm_4_1`, and descriptive slugs for unnumbered items. Inventory every source
item, including footnotes and proofs preceding their statements. Each occurrence
has a unique source label and explicit disposition. Omission requires a reason;
a page is complete only after its referenced nodes exist. Merged ids are
permanent; pruning an unused auxiliary/cited node leaves a tombstone.

`source.pages` contains printed page numbers, including all proof pages. The PDF
index is printed page plus `document.pdf.page_offset`. Chapter and section are
source coordinates, not directory names. For articles represented by chapter
entries without child sections, omit `section`. Source ordering uses the page
inventory when available, then source coordinates and natural identifier order.

Imports precede the first module documentation comment. That comment starts with
a `yaml node` fenced block containing only authored fields. It contains no nested
Lean comment delimiters. YAML uses version 1.2, without anchors, aliases, tags,
merge keys or duplicate keys. Quote strings that look like dates or numbers.

Markdown sections appear in this order: Statement, Statement (original), Statement
(corrected), Proof, Description, Formalization notes, History. Statement and
Description are required; theorem-like nodes also require Proof. A source in a
language other than English additionally requires Statement (original).

Statement and Proof preserve verbatim source prose with semantics-preserving
typesetting and editorial brackets. Corrections belong in Statement (corrected)
with an explicit erratum deviation. Do not silently repair the author's claim.

`Aux_*` nodes support another node, `Bridge_*` nodes relate a source construction
to a counterpart, and `Cited_*` nodes represent results used but not proved by the
document. Cited nodes can remain unproved; their dependent status will distinguish
unresolved citations from unfinished internal proofs.

## Generated records

`homalg gen-roots` writes sorted imports and omits `Aux_*`/`Cited_*` from document
roots. `homalg extract` updates authored records and preserves existing derived
records, which are `null` until a Lean export has populated them. Never edit these
generated files by hand.

The remaining pipeline is `export-lean`, `index`, `site-data`. Compiled exports
provide statement/meaning hashes, declaration references, direct and transitive
`sorry`, and axioms. `nodes.json` stores reproducible document-local facts; global
closure, claim views and site projections belong in `build/`. Do not hand-edit
generated roots, JSON, blueprint TeX or TypeScript contracts.

Headlines separate in-progress, statement-complete, proof-complete and confirmed
error. Detailed states distinguish internal unfinished dependencies, cited
dependencies and nonstandard axioms. Text containing no `sorry` is not evidence
of a complete proof or an approved statement. A reviewed statement can be
statement-complete while its proof remains unfinished; informal items and pruned
auxiliaries have no headline.

## Lean proof discipline

Import specific Mathlib modules; `import Mathlib` is forbidden. Avoid global
instances involving source-defined types, which can alter unrelated elaboration.
Every remaining `sorry` belongs to a named theorem with a source and natural
language proof. Hollow definitions, disguised axioms, trivial placeholders and
assumptions packaging the intended conclusion do not establish formalization.

`decls` names every principal declaration. Classify source dependencies as
`deps.statement` or `deps.proof`. Definition/construction bodies contribute
statement dependencies; theorem proof bodies contribute proof dependencies.
Retain source-route imports even when the current Lean proof bypasses them:
repair the route or document a deviation. `fix-deps` adds verified dependencies,
not deletions. Inspect both sides of `deps_diff` and explain remaining mismatches.

A choice-of-representative deviation needs an explicit comparison. A proof-route
deviation explains the bypassed source steps. Cited nodes identify the work and
locator, or explicit folklore provenance, and where the source invokes it.
Editorial formulations must be marked. Never relabel a source lemma as cited just
to remove an internal proof blocker. Substantial supporting lemmas get nodes.

## Transcription and review evidence

Scanned transcription uses vision only. Extracted text is navigation material,
not mathematical evidence. Private pages record source, PDF index, retrieval date
and transcriber provenance. Landing and independent review bind to the file's
SHA-256; later edits reopen the page. Reviewer and transcriber session identities
must differ. Disputed pages require human adjudication.

Independent fidelity reports live in `literature/KEY/reviews/LocalId.md`. Honesty
checks cover hidden assumptions, weakened claims and vacuity as well as textual
agreement. `review-fidelity` requires current satisfactory evidence and current
compiled facts. Changing the statement reopens its lock. First-chapter definitions,
foundation and explained-deviation nodes accept independent agent reviews under
the enabled policy. Unresolved mathematical or source disagreements still require
owner adjudication. An agent review never implies human approval.

`dispute open` records a problem and local inbox request. A raised dispute differs
from a confirmed source error; only `dispute confirm` writes the latter. Resolution
preserves history through an erratum, a proof-route change, or withdrawal. Human
commands require an interactive terminal, no agent-session marker and no active
run, then record the change in the local ledger. Agents must not simulate these
conditions or invent approvals.

## Validation and publication

Use `validate --fast` while editing. Full validation checks compiled facts and
locks under the shared workspace lock. PR policy checks additionally need the
real base, author, labels and review context. `summary.skipped` lists unavailable
checks; success with skipped private-source/PR checks is not a merge approval.
Run `make test`, `make validate` and `make site` before reporting completion.

Search existing tags and concepts before adding them. Relations need source
evidence, review state, canonical orientation and retained alias history. The
site hides unreviewed relations by default. Evolution summaries are attributable
outputs bound to a deterministic bundle; changed inputs make them stale. An
evolution review does not turn a conjectural conceptual link into a Lean theorem.

Formalization stays inside the claimed document and explicit task scope.
Infrastructure and vocabulary maintenance have their own PR category. Keep
PDFs, images, full private transcriptions, credentials, engine ledgers and raw
conversations out of public Git. See [submit](playbooks/submit.md) for publication
and [IMPLEMENTATION.md](IMPLEMENTATION.md) for current acceptance and remaining
mathematical and deployment work.
