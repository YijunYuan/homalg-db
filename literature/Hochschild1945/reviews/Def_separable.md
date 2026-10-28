# Independent review: source separability

## source-fidelity — 2026-10-28 — ci-separability-independent
Session: ci-separability-independent
Author-session: codex-schema-taxonomy-2026-10-28
Status: satisfactory
Verdict: The current declaration preserves finite-basis scalar extension, its induced multiplication, every extension field, and the finite-dimensional nonunital semisimplicity boundary. The radical interpretation is justified below independently of any cohomology criterion.

| Original source and location | Current node excerpt | Comparison |
| --- | --- | --- |
| Printed pp. 60–61 / PDF pages 4–5, definition at the section boundary | Statement begins with the preceding page's word and retains the finite linear combination, basis and multiplication clauses | Compared with the reviewed transcription and page 5 image; no mathematical clause omitted. |
| Printed p. 61, footnote 7 | The classical algebra reference boundary is retained | No later cohomology result is treated as part of this definition. |

| Source hypothesis or conclusion | Lean expression | Comparison |
| --- | --- | --- |
| Arbitrary ground field and associative algebra, with finite basis | `Field K`, `NonUnitalRing A`, `Module K A`, scalar compatibility, `FiniteDimensional K A` | No identity, characteristic, perfection or algebraic closure restriction is added. |
| Every extension field | All `Γ : Type u`, `[Field Γ]`, `[Algebra K Γ]` | Every extension in the ambient universe; the field algebra map is automatically injective. This ordinary universe convention is explicit in the notes. |
| All linear combinations of the chosen finite basis | `BasisExtension n Γ` and `basisExtensionEquiv b Γ` | Actual coordinate vector space with the basis expansion proved in the bridge. |
| Multiplication derived from original basis products | `basisExtensionMul b Γ`; bridge `basisExtensionMul_coordinates` | Full structure-constant formula is proved, ruling out accidental pointwise multiplication. |
| Scalar extension is semisimple | `Semisimple Γ (BasisExtension n Γ)` | Finite-dimensional radical-zero condition; the zero algebra is included. |

| Definition used by the statement | Construction / foundation boundary | Lean meaning |
| --- | --- | --- |
| `Semisimple K A` | Classical finite-dimensional radical theory; independent reasoning below | Preimage under `Unitization.inr` of the unitization's Jacobson radical is zero. |
| `Unitization K A` | Pinned Mathlib `Algebra/Algebra/Unitization.lean` | Underlying `K × A`, product `(r,a)(s,b)=(rs,r•b+s•a+a*b)`. No identity is inserted into A itself. |
| `Ring.jacobson` | Pinned Mathlib `RingTheory/Jacobson/Radical.lean` | Infimum of maximal left ideals, not maximal two-sided ideals. |
| Scalar extension | Elementary tensor product and finite basis boundary | The bridge proves agreement of both the vector space and its multiplication. |

### Independent radical-boundary justification

Let U=K⊕A with the displayed unitization product. The map a↦(0,a) is injective and identifies A with a two-sided ideal of U. This follows directly from the product, and agrees with the pinned Mathlib lemmas `Unitization.inr_injective`, `inr_mul`, `inl_mul_inr` and `inr_mul_inl`.

For finite-dimensional U, its Jacobson radical is nilpotent and contains every nilpotent two-sided ideal. These are the equivalent characterizations in A. G. Cox's author-hosted lecture notes, Theorem 2.3.4, printed p. 22 ([primary source](https://www.staff.city.ac.uk/a.g.cox/LTCC/Week2.pdf)). The same theorem identifies radical zero with semisimplicity in the finite-dimensional setting.

The following argument is the reviewer's deduction, not a quoted theorem or an additional Lean axiom. Every K-linear two-sided ideal N of A is also an ideal of U: multiplication by (r,a) adds only scalar multiples and A-products. If N is nilpotent in A, its embedded copy is nilpotent in U, hence lies in J(U). Conversely, A∩J(U) is a nilpotent two-sided ideal of A because J(U) is nilpotent. Thus A∩J(U) is exactly the largest nilpotent ideal of A, the classical finite-dimensional radical. Requiring its preimage to be zero is the source's semisimplicity condition. This argument works over any field, and does not require A to have an identity.

As a separate corroboration, Almus–Blecher–Read explicitly discuss preservation of the Jacobson radical by unitization as a fact of pure algebra on printed p. 68 ([publisher PDF](https://www.impan.pl/shop/en/publication/transaction/download/product/90565)). Their operator-algebra setting is not used to impose a topology or restrict the ground field here.

Limits: the elementary classical radical interpretation is an approved-foundation candidate, with this independent mathematical justification; this review does not claim that the equivalence with every possible semisimplicity convention has itself been proved in Lean. The finite-dimensional typeclass is essential and is present. No cohomology-vanishing or existence-of-identity conclusion is built into the predicate.

## honesty — 2026-10-28 — ci-separability-independent
Session: ci-separability-independent
Author-session: codex-schema-taxonomy-2026-10-28
Status: satisfactory
Verdict: The coordinate algebra contains actual transported ring operations and proved compatibility laws. The semisimplicity predicate is an explicit classical foundation interpretation, not an input field containing a later theorem.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| `basisExtensionRing`, scalar laws | Constructed algebra structure | Transport through an actual linear equivalence; associativity and distributivity are proved, not accepted as parameters. |
| `sourceSeparable` | Source definition | Quantifies extension fields and tests the constructed algebra; no cohomology assumption occurs. |
| `Semisimple` | Explicit classical foundation boundary | Finite-dimensional radical-zero condition justified above. |
| Proof dependencies | No unfinished declaration found | Current definition and bridge compile without `sorry`; no added mathematical axiom or hidden theorem conclusion was found. |
