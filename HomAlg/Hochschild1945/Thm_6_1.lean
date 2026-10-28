import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Con_extension_module
import HomAlg.Hochschild1945.Aux_Thm_6_1_finite_support
import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Prop_6_1
import HomAlg.Hochschild1945.Prop_6_2
import HomAlg.Hochschild1945.Prop_6_3

/-!
```yaml node
id: "Hochschild1945.Thm_6_1"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Theorem 6.1"
  pages:
    - 67
  chapter: "6"
tags:
  - "algebra-extension"
  - "hochschild-cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_extension"
    - "Hochschild1945.Aux_Thm_6_1_finite_support"
    - "Hochschild1945.Con_extension_module"
    - "Hochschild1945.Prop_6_1"
    - "Hochschild1945.Prop_6_2"
    - "Hochschild1945.Prop_6_3"
decls:
  - "Hochschild1945.segregated_iff_second_cohomology_vanishes"
fidelity:
  status: "deviates"
  deviations:
    - kind: "generality"
      what: "Universal segregation quantifies finite-dimensional extension algebras explicitly; coefficient
        modules remain arbitrary."
      why: "The classical radical argument uses finite dimension, and unrestricted extensions give counterexamples
        such as K[x] onto K×K. The theorem's arbitrary-coefficient implication is retained using an explicit
        finite-support reduction."
    - kind: "proof-route"
      what: "The forward implication restricts a cocycle to a finite-dimensional stable coefficient submodule
        and directly extracts a primitive from a splitting, bypassing Proposition 6.2's full class bijection."
      why: "This supplies the missing dimension reconciliation while preserving arbitrary coefficient
        modules and the source extension-to-coboundary argument."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.segregated_iff_second_cohomology_vanishes:
        statement_sha256: "64c7785f6326cc294775ee1ef03e17282aa30defc70c4b554b41b5540ad33831"
        type_hash: "000000009245af93"
        meaning_hash: "c28126fce9631a58"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Segregation and second cohomology"
```

## Statement

A necessary and sufficient condition for $\mathfrak{A}$ to be segregated in every extension is that $H^2(\mathfrak{A},\mathfrak{P})=\{0\}$, for every two-sided $\mathfrak{A}$-module $\mathfrak{P}$.

## Proof

From Propositions 6.1, 6.2, and 6.3 follows immediately the main result of this section: [uses `Hochschild1945.Prop_6_1`] [uses `Hochschild1945.Prop_6_2`] [uses `Hochschild1945.Prop_6_3`]

[uses `Hochschild1945.Aux_Thm_6_1_finite_support`] [uses `Hochschild1945.Con_extension_module`] [uses `Hochschild1945.Def_extension`]

## Description

Characterizes segregation in every extension by vanishing of second cohomology for every bimodule.
## Formalization notes

The universal extension assertion is interpreted for finite-dimensional extension
algebras; the general extension definition itself has no dimension restriction.
This scope is necessary: evaluation at 0 and 1 maps K[x] onto the separable
algebra K×K, but no algebra section can produce a nontrivial idempotent in K[x].
Coefficient modules are still arbitrary. Theorem 6.1's forward direction uses
the additional finite-support reduction proved in its technical auxiliary.
The explicit clarification is recorded as a deviation for independent review.
[uses `Hochschild1945.Aux_Thm_6_1_finite_support`]

The source cites Propositions 6.1–6.3 collectively. The forward Lean proof
constructs the finite cocycle extension and extracts a primitive from its algebra
section directly; the reverse implication uses the explicit class criterion of
Proposition 6.3 and Proposition 6.1. It does not invoke Proposition 6.2's full
classification bijection. That source dependency is retained in the header and
import, with its generated `deps_diff.declared_not_verified.proof` entry explained by the
recorded proof-route deviation. No formal usage is manufactured.


The principal statement names SegregatedInEveryExtension from Prop_6_1.
Def_extension is used directly in the proof's actual extension arguments and
finite-support construction, so it is recorded under proof dependencies rather
than as an additional direct statement dependency. This classification does not
change the extension predicate or its finite-dimensional scope. The separate
source-only Prop_6_2 edge remains explained by the proof-route deviation above.

-/

namespace Hochschild1945

universe u

variable (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]

/-- Second cohomology vanishes for every source bimodule, including infinite-dimensional ones. -/
def SecondCohomologyVanishes : Prop :=
  ∀ (P : Type u) [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P),
    Subsingleton (Cohomology M 2)

/-- The forward finite-support reduction: close the finite-dimensional image of a
2-cocycle under left and right A-actions. Its stable span is finite-dimensional
because it is generated by v, a·v, v·a, and (a·v)·b. Apply segregation to the finite
cocycle extension of this submodule, then include its primitive back into P.
This explicit additional reduction is proved in the finite-support auxiliary. -/
theorem secondCohomologyVanishes_of_segregated
    (h : SegregatedInEveryExtension K A) : SecondCohomologyVanishes K A := by
  intro P _ _ M
  apply FiniteSupport.cohomology_subsingleton_of_finite_extensions M
  intro B _ _ _ _ _ E _
  exact h B E

/-- The source implication from vanishing H² through singular extensions and
Proposition 6.1. The singular step uses the actual quotient class of a section. -/
theorem segregated_of_secondCohomologyVanishes
    (h : SecondCohomologyVanishes K A) : SegregatedInEveryExtension K A := by
  apply segregatedInEveryExtension_of_singular
  intro B _ _ _ _ _ E hE
  obtain ⟨ρ,hρ⟩ := E.linear.exists_rightInverse_of_surjective
    (LinearMap.range_eq_top.mpr E.surjective)
  have hs : ∀ a, E.sigma (ρ a) = a := fun a => LinearMap.congr_fun hρ a
  apply (Extension.isSegregated_iff_sectionClass_zero E hE ρ hs).mpr
  letI := h E.kernel (E.kernelModule hE ρ hs)
  exact Subsingleton.elim _ _

/-- **Theorem 6.1** (Hochschild), with its finite-dimensional extension scope
explicit. Coefficient modules remain arbitrary; the forward implication requires
the documented finite-support reduction. -/
theorem segregated_iff_second_cohomology_vanishes :
    SegregatedInEveryExtension K A ↔ SecondCohomologyVanishes K A :=
  ⟨secondCohomologyVanishes_of_segregated K A, segregated_of_secondCohomologyVanishes K A⟩

end Hochschild1945
