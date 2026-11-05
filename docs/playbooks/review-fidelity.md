# Review statement fidelity

Review the current compiled declarations against the original page images and
reviewed transcription. Read [CONVENTIONS.md](../CONVENTIONS.md) first. A plausible
Lean type, successful build or existing lock does not establish source fidelity.
Inspect all definitions used by the statement until the document's approved
`foundations` boundary. Check the proof route separately from the statement.

For a parallel batch, first verify the author's frozen handoff and your actual
independence from every node you will review. Read the exact supplied source and
candidate inputs, including recursive dependencies. The author's preparation
check is neither your verdict nor permission to reuse a report after edits.
Keep a separate substantive report for each node; split work when actual author
or reviewer provenance differs. See [PARALLEL_WORKFLOW.md](../PARALLEL_WORKFLOW.md).

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

After actual satisfactory reports for the stable authored nodes, freeze the final
inputs and register one batch for each real author/reviewer pair:

```sh
homalg workflow review-snapshot build/author-delivery-001.json \
  --node ACTUAL_NODE_ID --out build/review-inputs-001.json
homalg review-fidelity-batch ACTUAL_NODE_ID --by ACTUAL_REVIEWER \
  --session ACTUAL_REVIEW_SESSION --author-session ACTUAL_AUTHOR_SESSION \
  --snapshot build/review-inputs-001.json
```

Repeat `--node` and the ordered positional list for several nodes. The final
snapshot must include the completed reports; the earlier author handoff does not
bind reports that had not yet been written. Registration shares one fresh
build/export for that operation while retaining each node's source/type/meaning
hashes, report and lock. It refuses planned nodes, unsatisfactory or missing
evidence, self-review, stale inputs and protected human changes. Required honesty
blocks must carry the same genuine provenance. It has no batch human override.

The standalone `review-fidelity-snapshot NODE_ID... --out build/NEW.json` is
available when no author-handoff linkage is needed. The existing single-node
`review-fidelity` command remains compatible. A snapshot or successful build
cannot replace your actual source comparison. Stop after a failed registration,
retain its journal, and preserve old reports with an explicit explanation of any
correction or withdrawn finding. Read the exact input and recovery contract in
[PARALLEL_WORKFLOW.md](../PARALLEL_WORKFLOW.md).

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
