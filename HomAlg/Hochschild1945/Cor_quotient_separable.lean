import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Aux_Thm_5_1_quotient_module
import HomAlg.Hochschild1945.Thm_5_1
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Lem_delta_delta_zero
import HomAlg.Hochschild1945.Aux_Def_2_1_formula
import HomAlg.Hochschild1945.Thm_4_1

/-!
```yaml node
id: "Hochschild1945.Cor_quotient_separable"
doc: "Hochschild1945"
kind: "corollary"
source:
  label: "Corollary (p. 64)"
  pages:
    - 64
  chapter: "5"
tags:
  - "hochschild-cohomology"
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Def_natural_homomorphism"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Aux_Thm_5_1_quotient_module"
    - "Hochschild1945.Def_2_3"
  proof:
    - "Hochschild1945.Thm_5_1"
    - "Hochschild1945.Thm_4_1"
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Lem_delta_delta_zero"
    - "Hochschild1945.Aux_Def_2_1_formula"
decls:
  - "Hochschild1945.quotient_separable_iff_restriction_injective"
fidelity:
  status: "deviates"
  deviations:
    - kind: "proof-route"
      what: "The proof uses existence of a descended corrected cocycle and a primitive, with inflation
        injectivity only for coefficient modules annihilated by the ideal."
      why: "The printed proof invokes Theorem 5.1, whose stronger kernel identification has a confirmed
        error witnessed by the explicit primitive-dependence counterexample."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.quotient_separable_iff_restriction_injective:
        statement_sha256: "93a90983b5726a132adc7aa06ec1ed5d36b18d72a4c449c8be5dba46bddee515"
        type_hash: "0000000073a8b554"
        meaning_hash: "0e4fdf9e05389f12"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/ci_governance"
title: "Separability of a quotient"
```

## Statement

A necessary and sufficient condition that $\mathfrak{A}/\mathfrak{B}$ be separable is that the natural homomorphism of $H^1(\mathfrak{A},\mathfrak{P})$ into $H^1(\mathfrak{B},\mathfrak{P})$ be an isomorphism, for every two-sided $\mathfrak{A}$-module $\mathfrak{P}$.

## Proof

We may also start with any two-sided $\mathfrak{A}/\mathfrak{B}$-module $\mathfrak{Q}$ and make it a two-sided $\mathfrak{A}$-module by the definitions: $a\cdot v=\bar a\cdot v$, $v\cdot a=v\cdot\bar a$, where $v\in\mathfrak{Q}$ and $\bar a$ is the coset of $a\bmod\mathfrak{B}$. Theorem 5.1 then shows that the kernel of the natural homomorphism of $H^1(\mathfrak{A},\mathfrak{Q})$ into $H^1(\mathfrak{B},\mathfrak{Q})$ is isomorphic with $H^1(\mathfrak{A}/\mathfrak{B},\mathfrak{Q})$. Combining these results with Theorem 4.1 we obtain the following corollary: [uses `Hochschild1945.Thm_5_1`] [uses `Hochschild1945.Thm_4_1`]

[uses `Hochschild1945.Aux_Def_2_1_formula`] [uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Def_2_2`] [uses `Hochschild1945.Def_cochain`] [uses `Hochschild1945.Lem_delta_delta_zero`]

## Description

Characterizes separability of a quotient through the natural restriction maps in first cohomology.
## Formalization notes

The source uses “isomorphism” in the historical sense of an injective homomorphism onto its image: the preceding argument proves a zero-kernel criterion, not surjectivity. Accordingly the Lean statement uses Function.Injective. The quotient is represented by a genuinely surjective algebra homomorphism π:A→C. The original proof paragraph is preserved.

The local proof is complete and contains no `sorry`. In the forward direction, subtract a primitive for the restriction to obtain a cocycle vanishing on the ideal. The cocycle identity puts its values in the two-sided annihilator, so it descends to a quotient cocycle. Theorem 4.1 supplies one primitive there, which combines with the first primitive. No choice-independent assignment of quotient cohomology classes is asserted. In the reverse direction, inflate any quotient cocycle to a quotient module regarded as an A-module. Its restriction is zero, so injectivity gives a primitive; surjectivity of π proves the same primitive works on C. Coefficient modules remain arbitrary.

Theorem 4.1 now has a complete local proof relative to its explicit classical cited boundaries. The false Theorem 5.1 is never invoked. Its source-only proof dependency remains declared and explained by the proof-route deviation (`deps_diff.declared_not_verified.proof`). Genuine kernel/annihilator constructions are isolated in Aux_Thm_5_1_quotient_module, which has no logical dependency on the false claim. The counterexample to Theorem 5.1 does not refute this corollary's universal quantification over every coefficient module.
-/

namespace Hochschild1945.CorollarySupport

open scoped TensorProduct

universe u
variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- Degree-one source cocycles are exactly bimodule derivations. -/
theorem cocycle_one_iff (M : TwoSidedModule K A P) (f : Cochain K A P 1) :
    IsCocycle M 1 f ↔ ∀ a b : A, f (a * b) = M.left a (f b) + M.right (f a) b := by
  constructor
  · intro h a b
    have heq := congrArg (fun g : Cochain K A P 2 => g (a ⊗ₜ[K] b)) h
    rw [delta_one_apply] at heq
    change M.left a (f b) - f (a * b) + M.right (f a) b = 0 at heq
    exact (sub_eq_zero.mp (by convert heq using 1; abel)).symm
  · intro h
    change delta M 1 f = 0
    apply TensorProduct.ext'
    intro a b
    rw [delta_one_apply]
    simp only [h a b, LinearMap.zero_apply]
    abel

/-- A zero first cohomology group is equivalent to every one-cocycle being inner. -/
theorem first_cohomology_vanishes_iff (M : TwoSidedModule K A P) :
    Subsingleton (Cohomology M 1) ↔
      ∀ f : Cochain K A P 1, IsCocycle M 1 f → IsCoboundary M 0 f := by
  constructor
  · intro h f hf
    have hzero : (Submodule.Quotient.mk (⟨f, hf⟩ : cocycles M 1) : Cohomology M 1) = 0 :=
      h.elim _ _
    have hmem := (Submodule.Quotient.mk_eq_zero (boundariesInCycles M 1)).mp hzero
    rw [mem_boundariesInCycles, mem_coboundaries] at hmem
    exact hmem
  · intro h
    have hz : ∀ x : Cohomology M 1, x = 0 := by
      intro x
      induction x using Submodule.Quotient.induction_on with
      | _ f =>
          apply (Submodule.Quotient.mk_eq_zero (boundariesInCycles M 1)).mpr
          rw [mem_boundariesInCycles, mem_coboundaries]
          exact h f f.property
    exact ⟨fun x y => (hz x).trans (hz y).symm⟩

end Hochschild1945.CorollarySupport

namespace Hochschild1945.CorollarySupport

universe u
variable {K A C P : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]
  [FiniteDimensional K C]
  [AddCommGroup P] [Module K P]

attribute [local instance] idealFiniteDimensional

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [SMulCommClass K C C] [IsScalarTower K C C] [FiniteDimensional K C] in
/-- In degree one pullback is ordinary composition of linear maps. -/
theorem restrict_one_apply (π : A →ₙₐ[K] C) (f : Cochain K C P 1) (a : A) :
    restrictCochain π 1 f a = f (π a) := by
  have h := restrictCochain_evaluate π 1 f (PUnit.unit, a)
  simpa only [evaluateCochain_pureTensor, cochainPureTensor, CochainArgs.map] using h

/-- Restriction is injective in H¹ precisely when any cocycle whose restriction
is inner was already inner. This uses the actual quotient map. -/
theorem restriction_injective_iff (M : TwoSidedModule K A P) (I : AlgebraIdeal K A) :
    Function.Injective (naturalHomomorphism M I 1) ↔
      ∀ f : Cochain K A P 1, IsCocycle M 1 f →
        IsCoboundary (restrictModule M (NonUnitalSubalgebraClass.subtype I.subalgebra)) 0
          (restrictCochain (NonUnitalSubalgebraClass.subtype I.subalgebra) 1 f) →
        IsCoboundary M 0 f := by
  let φ := NonUnitalSubalgebraClass.subtype I.subalgebra
  have hmap (f : cocycles M 1) :
      naturalHomomorphism M I 1 (Submodule.Quotient.mk f) =
        Submodule.Quotient.mk (restrictCocycles M φ 1 f) := rfl
  constructor
  · intro h f hf hinner
    have hzero : naturalHomomorphism M I 1
        (Submodule.Quotient.mk (⟨f, hf⟩ : cocycles M 1)) = 0 := by
      rw [hmap]
      apply (Submodule.Quotient.mk_eq_zero (boundariesInCycles (restrictModule M φ) 1)).mpr
      rw [mem_boundariesInCycles, mem_coboundaries]
      exact hinner
    have hz := h (hzero.trans (map_zero _).symm)
    have hm := (Submodule.Quotient.mk_eq_zero (boundariesInCycles M 1)).mp hz
    rw [mem_boundariesInCycles, mem_coboundaries] at hm
    exact hm
  · intro h
    apply LinearMap.ker_eq_bot.mp
    apply LinearMap.ker_eq_bot'.mpr
    intro x hx
    induction x using Submodule.Quotient.induction_on with
    | _ f =>
      rw [hmap] at hx
      have hm := (Submodule.Quotient.mk_eq_zero (boundariesInCycles (restrictModule M φ) 1)).mp hx
      rw [mem_boundariesInCycles, mem_coboundaries] at hm
      apply (Submodule.Quotient.mk_eq_zero (boundariesInCycles M 1)).mpr
      rw [mem_boundariesInCycles, mem_coboundaries]
      exact h f f.property hm

omit [SMulCommClass K C C] [IsScalarTower K C C] [FiniteDimensional K C] in
/-- A derivation that vanishes on the ideal has values in its annihilator. -/
theorem values_mem_annihilator (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (f : Cochain K A P 1) (hf : IsCocycle M 1 f)
    (hvanish : ∀ b, π b = 0 → f b = 0) (a : A) :
    f a ∈ idealAnnihilator M π := by
  have hd := (cocycle_one_iff M f).mp hf
  intro b hb
  constructor
  · have h := hd b a
    rw [hvanish (b * a) (by simp [hb]), hvanish b hb, map_zero, LinearMap.zero_apply,
      add_zero] at h
    exact h.symm
  · have h := hd a b
    rw [hvanish (a * b) (by simp [hb]), hvanish b hb, map_zero, zero_add] at h
    exact h.symm

/-- Descend a derivation vanishing on the ideal to the true annihilator module. -/
noncomputable def descendCocycle (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) (f : Cochain K A P 1) (hf : IsCocycle M 1 f)
    (hvanish : ∀ b, π b = 0 → f b = 0) :
    Cochain K C (idealAnnihilator M π) 1 :=
  LinearMap.liftOfSurjective (f := LinearMap.ofClass π) hπ
    ⟨f.codRestrict (idealAnnihilator M π) (values_mem_annihilator M π f hf hvanish), by
      intro b hb
      apply Subtype.ext
      exact hvanish b hb⟩

omit [SMulCommClass K C C] [IsScalarTower K C C] [FiniteDimensional K C] in
/-- The descended derivation evaluates to the original value on a representative. -/
@[simp] theorem descendCocycle_apply (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) (f : Cochain K A P 1) (hf : IsCocycle M 1 f)
    (hvanish : ∀ b, π b = 0 → f b = 0) (a : A) :
    (descendCocycle M π hπ f hf hvanish (π a) : P) = f a := by
  unfold descendCocycle
  erw [LinearMap.equivOfSurjective_apply]
  rfl

/-- The descended map is a cocycle by the same Leibniz identity. -/
theorem descendCocycle_isCocycle (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) (f : Cochain K A P 1) (hf : IsCocycle M 1 f)
    (hvanish : ∀ b, π b = 0 → f b = 0) :
    IsCocycle (quotientAnnihilatorModule M π hπ) 1
      (descendCocycle M π hπ f hf hvanish) := by
  apply (cocycle_one_iff _ _).mpr
  intro x y
  obtain ⟨a, rfl⟩ := hπ x
  obtain ⟨b, rfl⟩ := hπ y
  apply Subtype.ext
  simp only [← map_mul, quotientAnnihilatorModule,
    quotientLeft_apply, LinearMap.flip_apply, quotientRight_apply]
  change (descendCocycle M π hπ f hf hvanish (π (a * b)) : P) =
    M.left a (descendCocycle M π hπ f hf hvanish (π b)) +
    M.right (descendCocycle M π hπ f hf hvanish (π a)) b
  erw [descendCocycle_apply, descendCocycle_apply, descendCocycle_apply]
  exact (cocycle_one_iff M f).mp hf a b

/-- Vanishing H¹ for the quotient annihilator supplies a primitive for every
cocycle that vanishes on the ideal. No choice-independent kernel identification
is used or asserted. -/
theorem vanishing_on_kernel_inner (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π)
    (hH : Subsingleton (Cohomology (quotientAnnihilatorModule M π hπ) 1))
    (f : Cochain K A P 1) (hf : IsCocycle M 1 f)
    (hvanish : ∀ b, π b = 0 → f b = 0) : IsCoboundary M 0 f := by
  obtain ⟨v, hv⟩ := (first_cohomology_vanishes_iff _).mp hH
    (descendCocycle M π hπ f hf hvanish)
    (descendCocycle_isCocycle M π hπ f hf hvanish)
  refine ⟨(v : P), ?_⟩
  apply LinearMap.ext
  intro a
  have he := congrArg (fun g : Cochain K C (idealAnnihilator M π) 1 => (g (π a) : P)) hv
  erw [descendCocycle_apply, delta_zero_apply] at he
  simp only [quotientAnnihilatorModule, quotientLeft_apply, LinearMap.flip_apply,
    quotientRight_apply] at he
  rw [delta_zero_apply]
  exact he

/-- A separable quotient makes restriction injective by correcting an inner
restriction, descending the corrected cocycle, and finding one primitive. -/
theorem separable_restriction_injective (M : TwoSidedModule K A P)
    (π : A →ₙₐ[K] C) (hπ : Function.Surjective π) (hC : sourceSeparable K C) :
    Function.Injective (naturalHomomorphism M (kernelIdeal π) 1) := by
  apply (restriction_injective_iff M (kernelIdeal π)).mpr
  intro f hf hres
  obtain ⟨u, hu⟩ := hres
  let f' : Cochain K A P 1 := f - delta M 0 u
  have hf' : IsCocycle M 1 f' := by
    change delta M 1 (f - delta M 0 u) = 0
    rw [map_sub, (hf : delta M 1 f = 0), delta_delta_zero, sub_self]
  have hvanish : ∀ b, π b = 0 → f' b = 0 := by
    intro b hb
    have he := congrArg (fun g : Cochain K (kernelIdeal π).subalgebra P 1 => g ⟨b, hb⟩) hu
    rw [restrict_one_apply, delta_zero_apply] at he
    change f b = M.left b u - M.right u b at he
    change f b - (delta M 0 u) b = 0
    rw [delta_zero_apply, he, sub_self]
  have hH := (separable_iff_first_cohomology_vanishes K C).mp hC
    (idealAnnihilator M π) (quotientAnnihilatorModule M π hπ)
  obtain ⟨v, hv⟩ := vanishing_on_kernel_inner M π hπ hH f' hf' hvanish
  refine ⟨u + v, ?_⟩
  rw [map_add]
  change f - delta M 0 u = delta M 0 v at hv
  rw [← hv]
  abel

/-- For modules pulled back from the quotient, an inflated one-cocycle
restricts to zero; injectivity forces a primitive that descends by surjectivity. -/
theorem quotient_cocycles_inner_of_restriction
    (π : A →ₙₐ[K] C) (hπ : Function.Surjective π)
    (h : ∀ (P : Type u) [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P),
      Function.Injective (naturalHomomorphism M (kernelIdeal π) 1))
    (N : TwoSidedModule K C P) : Subsingleton (Cohomology N 1) := by
  apply (first_cohomology_vanishes_iff N).mpr
  intro f hf
  let M := restrictModule N π
  let fA := restrictCochain π 1 f
  have hfA : IsCocycle M 1 fA := by
    change delta (restrictModule N π) 1 (restrictCochain π 1 f) = 0
    rw [← restrictCochain_delta, (hf : delta N 1 f = 0), map_zero]
  have hzero : IsCoboundary
      (restrictModule M (NonUnitalSubalgebraClass.subtype (kernelIdeal π).subalgebra)) 0
      (restrictCochain (NonUnitalSubalgebraClass.subtype (kernelIdeal π).subalgebra) 1 fA) := by
    refine ⟨0, ?_⟩
    apply LinearMap.ext
    intro b
    rw [restrict_one_apply, map_zero]
    change (restrictCochain π 1 f) b = 0
    rw [restrict_one_apply, (b.property : π b = 0), map_zero]
  obtain ⟨u, hu⟩ := (restriction_injective_iff M (kernelIdeal π)).mp (h P M) fA hfA hzero
  refine ⟨u, ?_⟩
  apply LinearMap.ext
  intro c
  obtain ⟨a, rfl⟩ := hπ c
  have he := congrArg (fun g : Cochain K A P 1 => g a) hu
  change (restrictCochain π 1 f) a = (delta (restrictModule N π) 0 u) a at he
  rw [restrict_one_apply, delta_zero_apply] at he
  rw [delta_zero_apply]
  exact he

end Hochschild1945.CorollarySupport

namespace Hochschild1945
universe u
attribute [local instance] idealFiniteDimensional

/-- **Corollary (p. 64)** (Hochschild). The natural restriction is injective
for every coefficient bimodule exactly when the quotient is separable. The
repaired proof constructs one descended cocycle and primitive, and does not
assert or use the source's false choice-independent kernel identification.
Its only remaining mathematical proof boundary is Theorem 4.1. -/
theorem quotient_separable_iff_restriction_injective (K A C : Type u)
    [Field K]
    [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
    [FiniteDimensional K A]
    [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]
    [FiniteDimensional K C]
    (π : A →ₙₐ[K] C) (hπ : Function.Surjective π) :
    sourceSeparable K C ↔
      ∀ (P : Type u) [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P),
        Function.Injective (naturalHomomorphism M (kernelIdeal π) 1) := by
  constructor
  · intro h P _ _ M
    exact CorollarySupport.separable_restriction_injective M π hπ h
  · intro h
    apply (separable_iff_first_cohomology_vanishes K C).mpr
    intro P _ _ N
    exact CorollarySupport.quotient_cocycles_inner_of_restriction π hπ h N

end Hochschild1945
