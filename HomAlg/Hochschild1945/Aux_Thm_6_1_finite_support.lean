import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_extension_cocycle
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Con_cocycle_extension
import HomAlg.Hochschild1945.Aux_Def_extension_section
import HomAlg.Hochschild1945.Prop_6_1
import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.LinearAlgebra.TensorProduct.Finiteness
import Mathlib.RingTheory.TensorProduct.Finite


/-!
```yaml node
id: "Hochschild1945.Aux_Thm_6_1_finite_support"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Finite-support reduction for Theorem 6.1"
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
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Prop_6_1"
  proof:
    - "Hochschild1945.Aux_Def_extension_section"
    - "Hochschild1945.Con_cocycle_extension"
    - "Hochschild1945.Con_extension_cocycle"
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_extension"
decls:
  - "Hochschild1945.FiniteSupport.cocycle_coboundary_of_finite_extensions"
  - "Hochschild1945.FiniteSupport.cohomology_subsingleton_of_finite_extensions"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.FiniteSupport.cocycle_coboundary_of_finite_extensions:
        statement_sha256: "5498afa6e412eb39503ca34b3a7277f89121fb92667384ea4468d636ac4cfce9"
        type_hash: "000000003e011224"
        meaning_hash: "4faf7d31d172d949"
      Hochschild1945.FiniteSupport.cohomology_subsingleton_of_finite_extensions:
        statement_sha256: "95cc2b8a5a99ca548b25110b525981df872a10a2cb21d4a62605d0ea810d6472"
        type_hash: "00000000fcc9114b"
        meaning_hash: "570a4308357464ae"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
nl_proof_source:
  follows: "agent"
aux:
  parent: "Hochschild1945.Thm_6_1"
  kind: "technical"
  reason: "Close the finite cocycle image under both module actions before applying the finite-dimensional
    universal extension hypothesis."
```

## Statement

[Editorial auxiliary] Each degree-two cocycle with values in an arbitrary two-sided module takes values in a finite-dimensional submodule stable under both algebra actions.

## Proof

The tensor square of the finite-dimensional algebra has finite dimension, hence the cocycle image is finite-dimensional. Adjoin its left-action image, right-action image and mixed-action image. Associativity of the two actions and their commutation show that these four finite-dimensional spaces have a stable sum. Restrict the cocycle to that sum, apply the finite-dimensional singular extension hypothesis, and include its primitive into the original coefficient space. This supplies an explicit finite-support step for the source theorem.
[uses `Hochschild1945.Con_cocycle_extension`]
[uses `Hochschild1945.Aux_Def_extension_section`]

[uses `Hochschild1945.Con_extension_cocycle`] [uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Def_extension`]

## Description

Provides the finite-support step reconciling arbitrary coefficients with the finite-dimensional extension scope.
-/

namespace Hochschild1945
namespace FiniteSupport
attribute [local instance] CocycleExtension.addCommGroupStructure
  CocycleExtension.moduleStructure CocycleExtension.mulStructure
universe u
open scoped TensorProduct
variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]
variable (M : TwoSidedModule K A P) (V : Submodule K P)

/-- Linearize the left action on the starting subspace. -/
def leftMap : A ⊗[K] V →ₗ[K] P := TensorProduct.lift
  (LinearMap.mk₂ K (fun a (v : V) => M.left a v)
    (by intros; simp) (by intros; simp) (by intros; simp) (by intros; simp))

/-- Linearize the right action on the starting subspace. -/
def rightMap : V ⊗[K] A →ₗ[K] P := TensorProduct.lift
  (LinearMap.mk₂ K (fun (v : V) a => M.right v a)
    (by intros; simp) (by intros; simp) (by intros; simp) (by intros; simp))

/-- Linearize the mixed left-then-right action on the starting subspace. -/
def bothMap : (A ⊗[K] V) ⊗[K] A →ₗ[K] P :=
  TensorProduct.lift (M.right.comp (leftMap M V))

/-- The starting subspace and its three action images form the stable support. -/
def space : Submodule K P := V ⊔ (LinearMap.range (leftMap M V) ⊔
  (LinearMap.range (rightMap M V) ⊔ LinearMap.range (bothMap M V)))

/-- The support contains the original subspace. -/
lemma base_mem (v : V) : (v : P) ∈ space M V := Submodule.mem_sup_left v.property
/-- The support contains every left translate of a starting vector. -/
lemma left_mem (a : A) (v : V) : M.left a v ∈ space M V :=
  Submodule.mem_sup_right (Submodule.mem_sup_left ⟨a ⊗ₜ[K] v,rfl⟩)
/-- The support contains every right translate of a starting vector. -/
lemma right_mem (v : V) (a : A) : M.right v a ∈ space M V :=
  Submodule.mem_sup_right (Submodule.mem_sup_right (Submodule.mem_sup_left ⟨v ⊗ₜ[K] a,rfl⟩))
/-- The support contains every mixed translate of a starting vector. -/
lemma both_mem (a : A) (v : V) (b : A) : M.right (M.left a v) b ∈ space M V :=
  Submodule.mem_sup_right (Submodule.mem_sup_right (Submodule.mem_sup_right ⟨(a ⊗ₜ[K] v) ⊗ₜ[K] b,rfl⟩))

/-- The four-space support is finite-dimensional when its starting space is. -/
abbrev finiteDimensional [FiniteDimensional K V] : FiniteDimensional K (space M V) := by
  unfold space
  infer_instance

attribute [local instance] finiteDimensional

/-- The three bimodule laws make the four-space sum stable under the left action. -/
lemma left_closed (a : A) (x : P) (hx : x ∈ space M V) : M.left a x ∈ space M V := by
  have hL : ∀ t, M.left a (leftMap M V t) ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul b v => simpa [leftMap, M.left_assoc] using left_mem M V (a*b) v
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  have hR : ∀ t, M.left a (rightMap M V t) ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul v b => simpa [rightMap, M.left_right] using both_mem M V a v b
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  have hB : ∀ t, M.left a (bothMap M V t) ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul t c =>
      induction t using TensorProduct.inductionOn with
      | tmul b v =>
        simpa [bothMap, leftMap, M.left_assoc, M.left_right] using both_mem M V (a*b) v c
      | add t s ht hs => simpa [bothMap] using (space M V).add_mem ht hs
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  change x ∈ V ⊔ (LinearMap.range (leftMap M V) ⊔
    (LinearMap.range (rightMap M V) ⊔ LinearMap.range (bothMap M V))) at hx
  rcases Submodule.mem_sup.mp hx with ⟨v,hv,w,hw1,rfl⟩
  rcases Submodule.mem_sup.mp hw1 with ⟨l,⟨t,rfl⟩,w,hw2,rfl⟩
  rcases Submodule.mem_sup.mp hw2 with ⟨r,⟨s,rfl⟩,b,⟨q,rfl⟩,rfl⟩
  simpa using (space M V).add_mem (left_mem M V a ⟨v,hv⟩)
    ((space M V).add_mem (hL t) ((space M V).add_mem (hR s) (hB q)))

/-- The three bimodule laws make the four-space sum stable under the right action. -/
lemma right_closed (a : A) (x : P) (hx : x ∈ space M V) : M.right x a ∈ space M V := by
  have hL : ∀ t, M.right (leftMap M V t) a ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul b v => simpa [leftMap] using both_mem M V b v a
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  have hR : ∀ t, M.right (rightMap M V t) a ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul v b => simpa [rightMap, M.right_assoc] using right_mem M V v (b*a)
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  have hB : ∀ t, M.right (bothMap M V t) a ∈ space M V := by
    intro t
    induction t using TensorProduct.inductionOn with
    | tmul t c =>
      induction t using TensorProduct.inductionOn with
      | tmul b v => simpa [bothMap, leftMap, M.right_assoc] using both_mem M V b v (c*a)
      | add t s ht hs => simpa [bothMap] using (space M V).add_mem ht hs
    | add t s ht hs => simpa using (space M V).add_mem ht hs
  change x ∈ V ⊔ (LinearMap.range (leftMap M V) ⊔
    (LinearMap.range (rightMap M V) ⊔ LinearMap.range (bothMap M V))) at hx
  rcases Submodule.mem_sup.mp hx with ⟨v,hv,w,hw1,rfl⟩
  rcases Submodule.mem_sup.mp hw1 with ⟨l,⟨t,rfl⟩,w,hw2,rfl⟩
  rcases Submodule.mem_sup.mp hw2 with ⟨r,⟨s,rfl⟩,b,⟨q,rfl⟩,rfl⟩
  simpa using (space M V).add_mem (right_mem M V ⟨v,hv⟩ a)
    ((space M V).add_mem (hL t) ((space M V).add_mem (hR s) (hB q)))


/-- Restrict both actions to the explicitly stable finite-support space. -/
def bimodule : TwoSidedModule K A (space M V) where
  left := LinearMap.mk₂ K (fun a (x : space M V) => ⟨M.left a x, left_closed M V a x x.property⟩)
    (by intros; apply Subtype.ext; simp) (by intros; apply Subtype.ext; simp)
    (by intros; apply Subtype.ext; simp) (by intros; apply Subtype.ext; simp)
  right := LinearMap.mk₂ K (fun (x : space M V) a => ⟨M.right x a, right_closed M V a x x.property⟩)
    (by intros; apply Subtype.ext; simp) (by intros; apply Subtype.ext; simp)
    (by intros; apply Subtype.ext; simp) (by intros; apply Subtype.ext; simp)
  left_assoc a b x := Subtype.ext (M.left_assoc a b x)
  right_assoc x a b := Subtype.ext (M.right_assoc x a b)
  left_right a x b := Subtype.ext (M.left_right a x b)

/-- The original cocycle takes values in the stable span of its own finite image. -/
def lift (f : Cochain K A P 2) : Cochain K A (space M f.range) 2 :=
  f.codRestrict (space M f.range) (fun t => base_mem M f.range ⟨f t,⟨t,rfl⟩⟩)

/-- Restriction preserves the cocycle equation, because both actions are restrictions. -/
theorem lift_isCocycle (f : Cochain K A P 2) (hf : IsCocycle M 2 f) :
    IsCocycle (bimodule M f.range) 2 (lift M f) := by
  apply TensorProduct.ext_threefold
  intro a b c
  rw [delta_two_apply]
  apply Subtype.ext
  have h := LinearMap.congr_fun hf ((a ⊗ₜ[K] b) ⊗ₜ[K] c)
  rw [delta_two_apply] at h
  exact h

/-- An algebra section of the cocycle extension supplies a primitive directly:
its negative coefficient coordinate has coboundary equal to the cocycle. -/
theorem coboundary_of_segregated (f : Cochain K A P 2) (hf : IsCocycle M 2 f)
    (h : letI := CocycleExtension.ring M f hf
      let := CocycleExtension.scalarTower M f hf
      let := CocycleExtension.smulComm M f hf
      (CocycleExtension.extension M f hf).IsSegregated) : IsCoboundary M 1 f := by
  let := CocycleExtension.ring M f hf
  let := CocycleExtension.scalarTower M f hf
  let := CocycleExtension.smulComm M f hf
  obtain ⟨s,hs⟩ := (Extension.isSegregated_iff_hasSection _).mp h
  let g : A →ₗ[K] P := -((LinearMap.snd K A P).comp
    ((CocycleExtension.linearEquiv M f).toLinearMap.comp (LinearMap.ofClass s)))
  refine ⟨g, ?_⟩
  apply TensorProduct.ext'
  intro a b
  rw [delta_one_apply]
  have hfst (a : A) : (s a).fst = a := hs a
  have hmul := congrArg (fun x : CocycleExtension M f => x.snd) (s.map_mul a b)
  change (s (a*b)).snd = M.left (s a).fst (s b).snd +
    M.right (s a).snd (s b).fst + f ((s a).fst ⊗ₜ[K] (s b).fst) at hmul
  rw [hfst, hfst] at hmul
  change f (a ⊗ₜ[K] b) = M.left a (-(s b).snd) - (-(s (a*b)).snd) +
    M.right (-(s a).snd) b
  simp only [map_neg, LinearMap.neg_apply]
  linear_combination (norm := abel) -hmul

/-- **Auxiliary to Theorem 6.1** (Hochschild, editorial finite-support reduction).
Every arbitrary-coefficient two-cocycle is a coboundary if all finite-dimensional
singular extensions are segregated. -/
theorem cocycle_coboundary_of_finite_extensions
    (h : SegregatedInEverySingularExtension K A)
    (f : Cochain K A P 2) (hf : IsCocycle M 2 f) : IsCoboundary M 1 f := by
  let M₀ := bimodule M f.range
  let f₀ := lift M f
  have hf₀ : IsCocycle M₀ 2 f₀ := lift_isCocycle M f hf
  let := CocycleExtension.ring M₀ f₀ hf₀
  let := CocycleExtension.scalarTower M₀ f₀ hf₀
  let := CocycleExtension.smulComm M₀ f₀ hf₀
  let := CocycleExtension.finiteDimensional M₀ f₀
  have hsplit := h (CocycleExtension M₀ f₀) (CocycleExtension.extension M₀ f₀ hf₀)
    (CocycleExtension.extension_singular M₀ f₀ hf₀)
  obtain ⟨g,hg⟩ := coboundary_of_segregated M₀ f₀ hf₀ hsplit
  refine ⟨(space M f.range).subtype.comp g, ?_⟩
  apply TensorProduct.ext'
  intro a b
  rw [delta_one_apply]
  have he := LinearMap.congr_fun hg (a ⊗ₜ[K] b)
  rw [delta_one_apply] at he
  exact congrArg (fun x : space M f.range => (x : P)) he

/-- Every actual cohomology quotient class vanishes under the finite singular-extension hypothesis. -/
theorem cohomology_subsingleton_of_finite_extensions
    (h : SegregatedInEverySingularExtension K A) : Subsingleton (Cohomology M 2) := by
  change Subsingleton (cocycles M 2 ⧸ boundariesInCycles M 2)
  have hz : ∀ x : cocycles M 2 ⧸ boundariesInCycles M 2, x = 0 := by
    intro x
    induction x using Submodule.Quotient.induction_on with
    | _ c =>
      rw [Submodule.Quotient.mk_eq_zero]
      apply (mem_boundariesInCycles M 2 c).mpr
      apply (mem_coboundaries M 1 c).mpr
      exact cocycle_coboundary_of_finite_extensions M h c c.property
  exact ⟨fun x y => (hz x).trans (hz y).symm⟩

end FiniteSupport
end Hochschild1945
