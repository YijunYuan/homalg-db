# Review statement fidelity

Review the current compiled declarations against the original page images and
reviewed transcription. Read [CONVENTIONS.md](../CONVENTIONS.md) first. A plausible
Lean type, successful build or existing lock does not establish source fidelity.
Inspect all definitions used by the statement until the document's approved
`foundations` boundary. Check the proof route separately from the statement.

Append a block to `literature/<DocKey>/reviews/<LocalId>.md`:

```markdown
## source-fidelity — YYYY-MM-DD — reviewer-session
Session: reviewer-session
Author-session: actual-author-session
Status: satisfactory
Verdict: State exactly what was checked and whether it agrees.

| Source text and location | Current node excerpt | Comparison |
| --- | --- | --- |
| Exact relevant source text, printed/PDF page | Statement paragraph | Evidence |

| Source hypothesis or conclusion | Lean expression | Comparison |
| --- | --- | --- |
| Every object, quantifier, hypothesis and conclusion | Exact declaration fragment | Evidence |

| Definition used by the statement | Source construction / foundation boundary | Lean meaning |
| --- | --- | --- |
| Each definition, recursively | Source page or confirmed boundary entry | Evidence |
```

Replace the example verdict and rows with substantive evidence. Use one of the
five statuses: `satisfactory`, `partial`, `mismatch`, `unverified`, or
`needs-adjudication`. Findings name severity (`blocker`, `major`, `minor`, `note`),
the evidence and next step. A partial review lists what remains unchecked. Append
new reviews instead of rewriting earlier judgments.

For a new `structure`, `class` or `instance`, also append an `honesty` block in the
same format. Classify what it represents: a proved construction, conditional
interface, imported boundary, dependence on sorry/axioms, hollow object or
unverified claim. Check that a theorem has not merely been stored as a field of
its assumptions. If an honesty review exists, its latest verdict must also be
satisfactory before locking.

After a satisfactory review of a faithful node:

```sh
homalg review-fidelity Hochschild1945.Thm_4_1 --by reviewer \
  --session "$ARCHON_HORIZON_SESSION" --author-session actual-author-session
```

The command builds fresh exports and records source/type/meaning hashes. It
refuses planned nodes and missing or unsatisfactory evidence. Record the actual
review and author session identities in every new source-fidelity and honesty
block. The reviewer must be independent of the author; same-session reviews are
rejected.

The user override dated 2026-10-28 permits independent agent reviews of foundations,
first-chapter fidelity and explained deviations when
`horizon/review-policy.yaml` enables `allow_independent_agent_reviews`. This changes
the original human-only gate; it does not label an agent as human. To review a
foundation or record the first-chapter checkpoint, use:

```sh
homalg foundations review Hochschild1945 1 --by reviewer \
  --session reviewer-session --author-session actual-author-session \
  --report literature/Hochschild1945/reviews/foundations.md
homalg plan Hochschild1945 --early-review-ok --by reviewer \
  --session reviewer-session --author-session actual-author-session
```

A foundation report must name the specific entry's notion and provide substantive
comparison evidence. The command binds its confirmation to the complete entry
content. The early-review checkpoint requires the relevant current reviews; it
is not permission to skip them. If the independent-agent policy is disabled,
these original human gates remain in force. Agents never invoke `--human` or
`foundations confirm`, impersonate a human, or manually write protected locks.
Mirror a review into the local graph if useful, but graph reviews do not create
a fidelity lock.

A statement or compiled type change reopens its review; a changed referenced
definition requires examination of meaning-hash warnings. Correct the node and
review its new bytes. Never replace evidence with a manual hash edit. Suspected
source errors go through `homalg dispute open <NodeId> --kind statement|proof
--reason '...'`; only humans can confirm or resolve them.
