# Independent foundation review: nonunital radical

Session: ci-separability-independent
Author-session: codex-schema-taxonomy-2026-10-28

## source-fidelity — 2026-10-28 — ci-separability-independent
Status: satisfactory
Verdict: The proposed elementary radical interpretation agrees with finite-dimensional nonunital algebra. Its preimage construction is independently justified below, without assuming a cohomology criterion.

| Foundation notion | Proposed Mathlib boundary | Independent assessment |
| --- | --- | --- |
| Finite-dimensional nonunital semisimplicity and radical | Unitization, Unitization.inr, Ring.jacobson | Actual unitization multiplication and finite-dimensional nilpotent-radical characterization identify the preimage with the classical radical. |


Let U=K⊕A with the displayed unitization product. The map a↦(0,a) is injective and identifies A with a two-sided ideal of U. This follows directly from the product, and agrees with the pinned Mathlib lemmas `Unitization.inr_injective`, `inr_mul`, `inl_mul_inr` and `inr_mul_inl`.

For finite-dimensional U, its Jacobson radical is nilpotent and contains every nilpotent two-sided ideal. These are the equivalent characterizations in A. G. Cox's author-hosted lecture notes, Theorem 2.3.4, printed p. 22 ([primary source](https://www.staff.city.ac.uk/a.g.cox/LTCC/Week2.pdf)). The same theorem identifies radical zero with semisimplicity in the finite-dimensional setting.

The following argument is the reviewer's deduction, not a quoted theorem or an additional Lean axiom. Every K-linear two-sided ideal N of A is also an ideal of U: multiplication by (r,a) adds only scalar multiples and A-products. If N is nilpotent in A, its embedded copy is nilpotent in U, hence lies in J(U). Conversely, A∩J(U) is a nilpotent two-sided ideal of A because J(U) is nilpotent. Thus A∩J(U) is exactly the largest nilpotent ideal of A, the classical finite-dimensional radical. Requiring its preimage to be zero is the source's semisimplicity condition. This argument works over any field, and does not require A to have an identity.

As a separate corroboration, Almus–Blecher–Read explicitly discuss preservation of the Jacobson radical by unitization as a fact of pure algebra on printed p. 68 ([publisher PDF](https://www.impan.pl/shop/en/publication/transaction/download/product/90565)). Their operator-algebra setting is not used to impose a topology or restrict the ground field here.

Limits: the elementary classical radical interpretation is an approved-foundation candidate, with this independent mathematical justification; this review does not claim that the equivalence with every possible semisimplicity convention has itself been proved in Lean. The finite-dimensional typeclass is essential and is present. No cohomology-vanishing or existence-of-identity conclusion is built into the predicate.
