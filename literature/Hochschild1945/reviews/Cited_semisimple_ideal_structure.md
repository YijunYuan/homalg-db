## source-fidelity — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: The cited statement is exactly the ideal structure of a finite-dimensional semisimple algebra used on printed pp. 64–65. It is strictly weaker than the general-algebra lemma proved from it.

| Source usage / hypothesis | Lean expression | Independent comparison |
| --- | --- | --- |
| An ideal of B/R is semisimple, printed p. 64 | First conjunct of `cited_semisimple_ideal_structure` | The ambient semisimplicity is an explicit hypothesis, and the subobject is an actual scalar-closed two-sided ideal. |
| Complement the image of S in C/H, printed pp. 64–65 | `∃ J : AlgebraIdeal K A, IsCompl ...` | The complement is a two-sided ideal, and IsCompl requires both zero intersection and full sum as vector subspaces. |
| Semisimple ambient algebra | `hA : Semisimple K A` | Does not import the stronger general-ambient conclusion of Lem_semisimple_ideal_summand. |
| Source algebra conventions | Finite dimension, associative nonunital ring, compatible K action | The source standing scope is retained; the coefficient field is arbitrary. |

The [Editorial] statement and exact source-evidence paragraph were independently compared with private page-0008.png and page-0009.png. Both conjuncts correspond to the printed classical uses. The radical notion is the independently reviewed foundation rather than a substituted unital separability predicate.

Findings: none.

## honesty — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: One explicit cited `sorry` remains. No proof completion is claimed by this fidelity review.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| Ideal / complement | Actual mathematical structures | Subalgebra closure plus both absorption laws; IsCompl on actual underlying submodules. |
| Generality boundary | Explicit hypothesis | Ambient algebra must be semisimple; this is not the conclusion of the later general-ambient theorem repackaged as an assumption. |
| Proof status | External cited boundary | One visible `sorry`, no added mathematical axiom. |
