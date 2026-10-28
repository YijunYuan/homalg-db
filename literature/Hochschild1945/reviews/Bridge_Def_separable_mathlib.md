# Independent review: scalar-extension bridge

## source-fidelity — 2026-10-28 — ci-separability-independent
Session: ci-separability-independent
Author-session: codex-schema-taxonomy-2026-10-28
Status: satisfactory
Verdict: The editorial bridge proves the actual source coordinate multiplication agrees with the nonunital tensor product. It preserves the selected basis and all structure constants and does not substitute the unital Mathlib separability predicate.

| Source construction / location | Current editorial statement | Comparison |
| --- | --- | --- |
| Printed p. 61 / PDF page 5, finite linear combinations with multiplication induced by basis products | Linear equivalence and explicit double-sum structure-constant formula | Precisely the claimed correspondence, with editorial status clear. |

| Statement clause | Lean declaration | Comparison |
| --- | --- | --- |
| Coefficient tuple represents its finite basis expansion | `basisExtensionEquiv_apply` | Proven sum of scaled elementary tensors. |
| Basis products retain structure constants | `basisExtensionMul_basis` | Coefficients are embedded by `algebraMap K Γ`. |
| Arbitrary coordinate multiplication | `basisExtensionMul_coordinates` | All i,j terms and the output coordinate k are present. |
| Equivalence preserves multiplication | `basisExtension_tensor_equivalence` | Actual linear equivalence plus multiplicativity, not mere equicardinality. |

| Referenced definition | Boundary / construction | Meaning checked |
| --- | --- | --- |
| `basisExtensionMul` | Independently reviewed `Def_separable` | Multiplication transported from the nonunital tensor algebra. |
| Tensor product and finite basis | Elementary foundation boundary | No unital algebra structure on A is assumed. |

## honesty — 2026-10-28 — ci-separability-independent
Session: ci-separability-independent
Author-session: codex-schema-taxonomy-2026-10-28
Status: satisfactory
Verdict: All three main bridge declarations have actual proofs. The coordinate expansion and basis-product proofs substantiate the transferred multiplication; the final equivalence is the already constructed map.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| Main bridge declarations | Proved correspondence | Explicit sum calculations and equivalence inverse identities; no `sorry`, new axiom or theorem conclusion packaged as an assumption. |
| Scope | Editorial auxiliary bridge | Parent and reason are explicit; no claim to be another original source theorem. |
