# Independent review: Thm_4_1

## source-fidelity — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The separability/vanishing equivalence retains the source definitions and arbitrary coefficient modules.

Source: pp.61–63 / PDF5–7. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Algebra | Finite-dimensional A has associative bilinear multiplication with no identity assumed. |
| Separability | sourceSeparable uses original basis scalar extensions and the confirmed radical convention. |
| Cohomology | Cohomology M 1 is the authored cocycle/boundary quotient, and Subsingleton means its zero group. |
| Quantifiers | Every P and actual TwoSidedModule M is quantified; P has no finite-dimensional or unital-action restriction. |
| Proof boundary | The source matrix-unit/descent and complementary-representation/inseparable-center route is recorded. The main proof remains one honest named sorry with typed citation dependencies. |

## honesty — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The separability/vanishing equivalence retains the source definitions and arbitrary coefficient modules.

Source: pp.61–63 / PDF5–7. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Algebra | Finite-dimensional A has associative bilinear multiplication with no identity assumed. |
| Separability | sourceSeparable uses original basis scalar extensions and the confirmed radical convention. |
| Cohomology | Cohomology M 1 is the authored cocycle/boundary quotient, and Subsingleton means its zero group. |
| Quantifiers | Every P and actual TwoSidedModule M is quantified; P has no finite-dimensional or unital-action restriction. |
| Proof boundary | The source matrix-unit/descent and complementary-representation/inseparable-center route is recorded. The main proof remains one honest named sorry with typed citation dependencies. |

The actual independent root-agent review is recorded under the enabled policy. It is not a human verdict. A normal review command must refresh compiled evidence before locking.

## source-fidelity — 2026-10-28 root-theorem41-final-independent

Session: root-theorem41-final-independent
Author-session: /root/ci_governance
Status: satisfactory
Verdict: Both implications retain the source constructions and arbitrary coefficient modules; the complete local proof uses only the separately identified classical citations.

The root reviewer inspected every helper in the assembled proof and compared
the final source excerpt and formalization notes with the original images of
PDF pages 5–7 (printed pages 61–63). The forward construction was authored by
`/root/lean_fixtures`; `/root/ci_governance` authored the converse and descent,
and performed the final integration. The reviewer authored neither implication.
This final review supersedes the earlier statement-only proof-boundary notes.

| Source clause or construction | Lean representation | Assessment |
| --- | --- | --- |
| Algebra and every two-sided module P | Nonunital finite-dimensional A over an arbitrary field; every actual `TwoSidedModule K A P` | Neither finite dimension nor unital actions are required of P. No perfection or characteristic-zero hypothesis is added. |
| Source separability and H¹ | `sourceSeparable K A` and the actual `Cohomology M 1` quotient | The statement retains the authored definitions. |
| Identity decomposition, p. 61 | `normalize_derivation`, with g(a)=e·f(a), u=f(e)−e·f(e) and the proved image condition | The source correction, including its sign, is explicit. Working on the same carrier does not impose an identity action on all of P. |
| Scalar extension and matrix-unit sum, p. 61 | `basechangeModule`, `basechange_derivation`, `basisExtensionEquiv`, `matrix_blocks_balance`, `balanced_family_inner` | Both actions are extended bilinearly; the displayed row/column sum is constructed and proved to be a primitive. Matrix-unit hypotheses are proved, not assumed. |
| Ground-field descent, p. 61 | `scalarContraction` and `inner_primitive_descends`, with K-linear τ and τ(1)=1 | Contraction commutes with both ground-field actions, giving the source's linear-system descent without a dimension restriction on P. |
| Complement and off-diagonal cocycle, p. 62 | `subspaceAction`, `complementAction`, `offDiagonal`, `complementHomModule` | These are the actual S_a, Q_a and Hom(S,Q) actions; their associativity and cocycle equations are proved. |
| Invariant graph s↦s−M₀(s), p. 62 | `corrected_projection_kernel`, `invariant_complement_of_inner_derivations` | The graph is proved to equal the corrected projection's kernel and to be complementary and invariant before applying the classical criterion. |
| Simple-component reduction, p. 62 | Actual ideal/retraction in `Cited_inseparable_simple_component`; `inner_derivations_on_retract` | The citation supplies no cohomological conclusion. Inflation and restriction of a primitive are proved locally. |
| Center and regular representation, pp. 62–63 | `center_one_is_identity`, center scalar structures, `regularMatrix`, `regularMatrix_injective` | Simplicity derives the unit; evaluation at that right identity proves the actual regular representation faithful. |
| Outer matrix cocycle, p. 63 | `matrixDerivative_mul`, `matrixBimodule`, `center_matrix_derivation_not_inner` | Lemma 4.1 is used within its reviewed finite-extension scope. The constructed derivation is nonzero on a center scalar, while every inner derivation vanishes there. |

The theorem uses the identity, splitting, representation, simple-component and
center citations, all explicitly identified classical facts. The later
`Def_natural_homomorphism` import contributes the authored ideal/restriction API;
the notes correctly distinguish this formalization dependency from an original
forward reference. The Statement and Proof retain the source text with editorial
dependency markers. There is no source-theorem shortcut through Theorem 5.1.

## honesty — 2026-10-28 root-theorem41-final-independent

Session: root-theorem41-final-independent
Author-session: /root/ci_governance
Status: satisfactory
Verdict: The main theorem and its local support lemmas contain complete proofs and genuine constructions, with no local sorry or added axiom.

| Check | Evidence | Assessment |
| --- | --- | --- |
| Hypothesis packaging | Actual tensor actions, finite matrix sums, projections, ideals and regular representations are constructed | No conclusion is stored as an input field; all hypotheses of the balanced-family helper are discharged. |
| Quotient semantics | `cocycle_one_iff` and `first_cohomology_vanishes_iff` unfold the authored cycle/boundary conditions | Vanishing is connected to the actual quotient, not assumed to mean universal innerness. |
| Proof closure | Both implications end in constructed local lemmas; the principal type is unchanged | No source result remains a local placeholder. The five classical cited boundaries are still external assumptions. |
| False source theorem | Theorem 5.1 is absent from both logical proofs | Its separately confirmed error is retained and never used to justify this theorem. |
| Independent evidence | Distinct author/reviewer executions, visual source comparison and the normal compiled review command | This is agent review under the approved policy, not a fabricated human approval. |

Targeted compilation of this theorem and both downstream corollaries succeeded.
The normal review command refreshes compiled evidence and checks the current
statement hashes before locking. Downstream corollaries now inherit the explicit
classical citations, rather than an unfinished local Theorem 4.1 proof.
