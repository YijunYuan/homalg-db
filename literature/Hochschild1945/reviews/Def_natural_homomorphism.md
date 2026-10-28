
## source-fidelity — 2026-10-28 — ci-section5-independent
Session: ci-section5-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: The principal definition constructs exactly the restriction map for a scalar-closed two-sided ideal, in every degree, on the source's actual cocycle/boundary quotients. The generalized pullback is an implementation helper with a proved evaluation identity.

| Source text and location | Current excerpt | Comparison |
| --- | --- | --- |
| Printed p. 63 / PDF page 7, first paragraph of section 5 | Statement retains the ideal, restricted module and cochain, preservation of cycles and boundaries, and resulting natural map | Independently compared with the page image and reviewed transcription. |

| Source hypothesis or conclusion | Lean expression | Comparison |
| --- | --- | --- |
| B is an ideal of A | `I : AlgebraIdeal K A` | A K-linear nonunital subalgebra with both absorption laws; this is an actual ideal argument. |
| Restrict the two actions to B | `restrictModule M (NonUnitalSubalgebraClass.subtype I.subalgebra)` | The original bilinear left and right actions are composed with the ideal inclusion. |
| Restrict each cochain argument | `restrictCochain`, `restrictCochain_evaluate` | Proved pointwise equality with evaluation on the included tuple. The genuine tensor/multilinear bridge preserves the original cochain carrier. |
| Cycles and boundaries restrict | `restrictCochain_delta`, `restrictCocycles`, `restrict_boundaries` | Commutation with δ is proved for every n using the independently reviewed alternating-sum formula. Boundary primitives are actually restricted, including degree zero separately. |
| Natural homomorphism on H^m | `naturalHomomorphism M I n` via `cohomologyPullback` | Actual linear map of Definition 2.3 quotients, constructed by `Submodule.mapQ`. |

| Definition used by statement | Source construction / foundation boundary | Meaning checked |
| --- | --- | --- |
| `TwoSidedModule`, `Cochain`, `delta` | Independently reviewed sections 1–2 | No unitality or finite dimension for P is added. |
| `Cohomology` | Definition 2.3 | Actual quotient of cocycles by the proved included boundary subspace. |
| `AlgebraIdeal` | Ordinary ideal background | Its fields specify precisely the ideal's defining data and laws. |
| Finite dimension of ideal | Subspace of finite-dimensional A | Derived using injectivity of inclusion; no extra restriction on the ideal. |

Findings: none. This construction is independent of the incorrect later Theorem 5.1. The dependency on the multilinear bridge and the alternating-sum auxiliary supplies the source's stated direct verification; it does not replace the natural map with a different cohomology construction.

## honesty — 2026-10-28 — ci-section5-independent
Session: ci-section5-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: The ideal structure contains only defining closure laws. All restriction maps, their differential compatibility and the final quotient map are constructed with actual proofs; no theorem conclusion is an input field.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| `AlgebraIdeal` | Genuine algebraic data | Scalar-closed subalgebra and left/right ideal absorption, with no cohomology claim stored as a field. |
| Restriction and quotient maps | Proved construction | Explicit functions and map laws, actual δ commutation and boundary witnesses. |
| Proof completeness | No local placeholder found | No `sorry` or added mathematical axiom in this node; inspected source route uses the previously proved tensor bridge and differential formula. |
