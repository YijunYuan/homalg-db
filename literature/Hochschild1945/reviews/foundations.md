# Independent foundation review

Session: root-foundations-independent
Author-session: /root/ci_governance

## source-fidelity — 2026-10-28 root-foundations-independent

Status: satisfactory
Verdict: Entries 1–10 describe elementary background used by the source and preserve its nonunital algebra and arbitrary coefficient-space boundaries. None imports a Hochschild definition or conclusion.

| Notion | Source evidence independently inspected | Scope and Lean comparison |
| --- | --- | --- |
| Sets and functions | Printed p. 59 / PDF 3 uses linear mappings; p. 64 / PDF 8 defines a homomorphism onto A. | `Set`, injectivity and surjectivity impose no extra algebraic laws. |
| Natural-number degrees and integer signs | Definition 2.1 on printed p. 59 gives finite indices and alternating powers of −1. | `Nat` and `Int` supply arithmetic; the actual coboundary and signs remain authored. |
| Ground fields | First sentence of section 1 says arbitrary field Φ. | `Field K` assumes no characteristic, perfection or algebraic closure. |
| Additive groups and vector spaces | First paragraph of section 1 calls P a linear space and distinguishes its two A-actions; footnote 4 refers the ordinary one-sided notions to Jacobson. | `Module K P` is a vector-space structure over K, not a unital action of A. |
| Associative algebras without an assumed identity | Printed p. 59 assumes an associative algebra; printed p. 61 derives an identity after assuming separability. | `NonUnitalRing A` with field-scalar compatibility expresses associative bilinear multiplication without an identity. |
| Finite bases of the algebra | Printed p. 59 chooses a₁,…,aₙ and gives nᵐ as the tensor-power dimension; printed p. 61 again uses a finite basis. | `Module.Basis` and `FiniteDimensional K A` express this context. There is no evidence here for adding `FiniteDimensional K P`, and the implementation does not add it. |
| Linear maps and linear isomorphisms | Printed pp. 59–60 use endomorphisms, linear mappings and the currying isomorphism; footnote 5 points to Jacobson pp. 4–5. | Elementary `LinearMap`/`LinearEquiv` are appropriate; source actions and cochains are separately defined. |
| Tensor products of vector spaces | Section 1's second paragraph defines the Kronecker-power basis explicitly. | `TensorProduct` models ordinary vector-space tensor products. The source's degree-zero convention and cochain construction remain explicit, with an independent multilinear comparison bridge. |
| Subspaces, additive subgroups and their quotients | Printed p. 60 defines cocycles, coboundaries and their quotient; printed pp. 62–64 uses kernels, subspaces and direct sums. | `Submodule`, `AddSubgroup`, quotient constructors, kernel and range provide elementary infrastructure, not preexisting cohomology. |
| Linear algebra homomorphisms and subalgebras | Section 6's first paragraph, printed p. 64, uses homomorphisms and complementary subalgebras in its definitions. | Nonunital homomorphisms/subalgebras avoid an unstated identity condition. Singularity, segregation and extension equivalence are source constructions. |

The reviewer inspected the private page images, the reviewed transcription, the
document entries and the corresponding Lean type assumptions. This report
approves only the ten named entries. The later radical/semisimplicity entry has
a separate author and requires its own independent report. It is not approved
by association with elementary linear algebra.

The finite-dimensional scope of the universal-extension statements in section 6
requires an explicit explanation and finite-support reduction. The approval of
elementary homomorphisms here does not approve those later theorem statements.

## honesty — 2026-10-28 root-foundations-independent

Status: satisfactory
Verdict: The ten entries supply elementary algebraic language and operations, with source evidence and stated limits. They contain no premise equivalent to a future cohomology theorem.

| Check | Evidence |
| --- | --- |
| No hidden conclusions | No source coboundary, cohomology, separability criterion or extension classification is imported as a foundation. |
| No extra module finiteness or unit | The source module remains arbitrary-dimensional with two explicitly authored, possibly nonunital actions. |
| Provenance | This is an independent root-agent review of entries authored by the ci_governance session, enabled by the owner's 2026-10-28 policy. It is not human approval. |
