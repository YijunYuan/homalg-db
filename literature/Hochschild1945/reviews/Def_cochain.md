# Independent review: Def_cochain

## source-fidelity — 2026-10-28 root-independent-pilot-review

Status: satisfactory
Verdict: The principal cochain space retains the source module context, degree-zero convention, and actual positive tensor powers. It does not replace the source with an imported Hochschild complex. Human review remains pending.

| Source evidence, printed p. 59 | Lean representation | Assessment |
| --- | --- | --- |
| Kronecker product of m underlying vector spaces | Iterated `TensorProduct K` in `KroneckerPower` | This is an actual tensor carrier; helper index n denotes n+1 factors and is documented. |
| Linear maps from the m-fold Kronecker power to P | `linearCochainSpace` in degree n+1 | The defining carrier is literal tensor-linear maps, not merely an assumed equivalent space. |
| A zero-cochain is an element of P | Degree zero is `ModuleCat.of K P` | The source convention is exact. |
| A and the two-sided module P established in the preceding paragraph | Principal `cochainSpace (M : TwoSidedModule K A P)` | The general carrier helpers are separate from the source-context principal declaration. Action values enter δ later, not the underlying vector space. |

The reviewer inspected the corrected source-context wrapper and compared the
statement with the independently reviewed private PDF page 3. The earlier
generality concern was resolved by retaining the general tensor helpers while
attaching the source's algebra/module hypotheses to the principal declaration.

## honesty — 2026-10-28 root-independent-pilot-review

Status: satisfactory
Verdict: The space is constructed from tensor products and linear maps, with no assumed cohomological properties or hollow definition.

| Check | Evidence | Assessment |
| --- | --- | --- |
| Actual carrier | Recursive tensor powers and linear-map spaces | Nontrivial source construction, not `Unit`, `True` or an axiom. |
| Context parameter | M restricts the source setting; its action values do not affect the carrier | Mathematically expected independence, explicitly documented. |
| Degree-zero boundary | P itself | No extra tensor representative silently changes the source convention. |


## source-fidelity — 2026-10-28 — ci-firstchapter-independent
Session: ci-firstchapter-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: The principal cochainSpace takes the source algebra and two-sided module context; positive degrees are linear maps from the iterated Kronecker product and degree zero is the coefficient space itself.

| Source location / text | Current source excerpt | Comparison |
| --- | --- | --- |
| Printed p. 59 / PDF p. 3, second paragraph; Kronecker powers, cochains and the degree-zero convention | Current Statement reproduces the paragraph | All three definitions and the basis description are retained. |

| Source hypothesis or conclusion | Lean representation | Comparison |
| --- | --- | --- |
| Source algebra and coefficient two-sided module | Principal `cochainSpace` takes `M : TwoSidedModule K A P` | Context is attached even though the underlying carrier does not depend on action values. |
| m positive tensor factors | `KroneckerPower K A n` has n+1 factors, recursively tensored on the right | The documented index shift gives exactly m factors for degree m. |
| Zero-cochain is an element of P | `linearCochainSpace 0 = ModuleCat.of K P` | The source special case is literal, without a forced degree-zero tensor model. |
| Positive cochain is a linear map | `linearCochainSpace (n+1) = ModuleCat.of K (KroneckerPower n →ₗ[K] P)` | This is the source construction; no pre-existing cohomology theory is substituted. |

| Definition used | Boundary / construction | Meaning checked |
| --- | --- | --- |
| `TwoSidedModule` | Previous authored source definition | Both actions and all compatibility laws are retained in the principal interface. |
| TensorProduct and LinearMap | Proposed elementary foundation boundary | Tensor association follows the last-factor currying used later by the source. |
| ModuleCat, Cochain and linearCochainSpace | Carrier/bundling helpers | No hidden proof assumptions or hollow data are introduced. |

Findings: none. This independent review records agent evidence only; it does not manufacture a human approval. The finite-dimensional algebra context is evidenced by the finite basis in the following paragraph on the same page, and the coefficient space is not silently restricted to finite dimension.

## honesty — 2026-10-28 — ci-firstchapter-independent
Session: ci-firstchapter-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: Actual recursive tensor and linear-map data, with a transparent context wrapper. The unused action values in the carrier are mathematically appropriate, and enter the later coboundary rather than being a hidden cohomology assumption.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| Main declarations and their referenced source definitions | Constructed data or proved source result | Actual recursive tensor and linear-map data, with a transparent context wrapper. The unused action values in the carrier are mathematically appropriate, and enter the later coboundary rather than being a hidden cohomology assumption. |

No sorry, extra asserted mathematical axiom, or theorem-conclusion packaging was found in these declarations and their source construction route. Compiled export was independently produced by the implementing math agent; this review additionally inspected the current Lean definitions/proofs and the reviewed source page.
