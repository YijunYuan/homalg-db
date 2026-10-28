import HomAlg.Hochschild1945.Def_natural_homomorphism
import HomAlg.Hochschild1945.Def_two_sided_module
import Mathlib.LinearAlgebra.Isomorphisms

/-!
```yaml node
id: "Hochschild1945.Aux_Thm_5_1_quotient_module"
doc: "Hochschild1945"
kind: "construction"
source:
  label: "Auxiliary to Theorem 5.1"
  pages: [63, 64]
  chapter: "5"
tags: ["hochschild-cohomology"]
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_natural_homomorphism"
    - "Hochschild1945.Def_two_sided_module"
  proof: []
decls:
  - "Hochschild1945.quotientAnnihilatorModule"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.quotientAnnihilatorModule:
        statement_sha256: "8b08a0114170ac6e8d1255fe15cb961a4494d33bda0f9c23c577d8d8bd221f2b"
        type_hash: "00000000bb7deaf8"
        meaning_hash: "ced76590c94a6228"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/ci_governance"
aux:
  parent: "Hochschild1945.Thm_5_1"
  kind: "technical"
  reason: "Separate the genuine quotient/annihilator constructions from the confirmed false kernel-isomorphism
    claim."
nl_proof_source:
  follows: "agent"
```

## Statement

[Editorial] Let π:A→C be a surjective homomorphism of the source algebras, and let P be a two-sided A-module. The kernel of π is a two-sided ideal. The subspace Q of elements annihilated on both sides by this ideal is stable under both A-actions, and these actions descend through π to make Q a two-sided C-module.

## Proof

The kernel is closed under scalars, addition and multiplication on either side by an arbitrary algebra element. For q in Q, the three bimodule associativity laws show that a·q and q·a remain in Q. Every kernel element acts as zero on Q. Therefore the two bilinear actions factor through the surjective quotient map, and their three associativity laws follow by choosing representatives in A.

## Description

Constructs the quotient-algebra module on the two-sided annihilator, independently of the erroneous kernel identification in Theorem 5.1.

## Formalization notes

These definitions and proofs were mechanically relocated from Thm_5_1.lean. The parent link records their source context; it is not a logical dependency on the false theorem. This construction neither asserts nor uses a choice-independent map from the restriction kernel to quotient cohomology. The coefficient module P remains arbitrary, with no finite-dimensional restriction.

The declared dependency on Def_natural_homomorphism records the actual
AlgebraIdeal interface used by the companion kernelIdeal construction in this
module. The listed principal declaration quotientAnnihilatorModule instead
expresses the annihilator directly by π(b)=0 and descends its actions without
calling kernelIdeal. Consequently the principal-declaration trace does not
include Def_natural_homomorphism; the retained
`deps_diff.declared_not_verified.statement` entry records this source/construction
context rather than an asserted direct use. No dependency on the false parent
claim is introduced.

-/

namespace Hochschild1945

universe u

variable {K A C P : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]
  [FiniteDimensional K C]
  [AddCommGroup P] [Module K P]

/-- The actual kernel ideal of a quotient-algebra presentation. -/
def kernelIdeal (π : A →ₙₐ[K] C) : AlgebraIdeal K A where
  subalgebra :=
    { carrier := {a | π a = 0}
      zero_mem' := map_zero π
      add_mem' := by intro a b ha hb; simp_all
      mul_mem' := by intro a b ha hb; simp_all
      smul_mem' := by intro r a ha; simp_all }
  mul_mem_left := by intro a b hb; change π b = 0 at hb; change π (a * b) = 0; simp [hb]
  mul_mem_right := by intro a b hb; change π b = 0 at hb; change π (b * a) = 0; simp [hb]

/-- The source's two-sided annihilator, not its generally larger centralizer. -/
def idealAnnihilator (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C) : Submodule K P where
  carrier := {p | ∀ b : A, π b = 0 → M.left b p = 0 ∧ M.right p b = 0}
  zero_mem' := by intro b hb; simp
  add_mem' := by intro p q hp hq b hb; simp [map_add, (hp b hb).1, (hp b hb).2,
    (hq b hb).1, (hq b hb).2]
  smul_mem' := by intro r p hp b hb; simp [map_smul, (hp b hb).1, (hp b hb).2]

omit [SMulCommClass K C C] [IsScalarTower K C C] [FiniteDimensional K C] in
/-- The annihilator is stable under the original left action. -/
theorem left_mem_idealAnnihilator (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (a : A) (p : idealAnnihilator M π) : M.left a p ∈ idealAnnihilator M π := by
  intro b hb
  constructor
  · rw [← M.left_assoc]
    exact (p.property (b * a) (by simp [hb])).1
  · rw [M.left_right, (p.property b hb).2, map_zero]

omit [SMulCommClass K C C] [IsScalarTower K C C] [FiniteDimensional K C] in
/-- The annihilator is stable under the original right action. -/
theorem right_mem_idealAnnihilator (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (a : A) (p : idealAnnihilator M π) : M.right p a ∈ idealAnnihilator M π := by
  intro b hb
  constructor
  · rw [← M.left_right, (p.property b hb).1]
    simp
  · rw [M.right_assoc]
    exact (p.property (a * b) (by simp [hb])).2

/-- Restrict the source actions to the two-sided annihilator subspace. -/
def annihilatorModule (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C) :
    TwoSidedModule K A (idealAnnihilator M π) where
  left :=
    { toFun := fun a =>
        { toFun := fun p => ⟨M.left a p, left_mem_idealAnnihilator M π a p⟩
          map_add' := by intros; apply Subtype.ext; simp
          map_smul' := by intros; apply Subtype.ext; simp }
      map_add' := by intros; ext; simp
      map_smul' := by intros; ext; simp }
  right :=
    { toFun := fun p =>
        { toFun := fun a => ⟨M.right p a, right_mem_idealAnnihilator M π a p⟩
          map_add' := by intros; apply Subtype.ext; simp
          map_smul' := by intros; apply Subtype.ext; simp }
      map_add' := by intros; ext; simp
      map_smul' := by intros; ext; simp }
  left_assoc := by intros; apply Subtype.ext; exact M.left_assoc _ _ _
  right_assoc := by intros; apply Subtype.ext; exact M.right_assoc _ _ _
  left_right := by intros; apply Subtype.ext; exact M.left_right _ _ _

/-- The kernel acts as zero on the annihilator on the left. -/
theorem annihilator_left_kernel (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C) :
    (LinearMap.ofClass π).ker ≤ (annihilatorModule M π).left.ker := by
  intro a ha
  apply LinearMap.ext
  intro p
  apply Subtype.ext
  exact (p.property a ha).1

/-- The kernel acts as zero on the annihilator on the right. -/
theorem annihilator_right_kernel (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C) :
    (LinearMap.ofClass π).ker ≤ (annihilatorModule M π).right.flip.ker := by
  intro a ha
  apply LinearMap.ext
  intro p
  apply Subtype.ext
  exact (p.property a ha).2

/-- Descend the actual left action through the surjective quotient map. -/
noncomputable def quotientLeft (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) : C →ₗ[K] idealAnnihilator M π →ₗ[K] idealAnnihilator M π :=
  LinearMap.liftOfSurjective (f := LinearMap.ofClass π) hπ
    ⟨(annihilatorModule M π).left, annihilator_left_kernel M π⟩

/-- Descend the actual right action, with the algebra argument first for lifting. -/
noncomputable def quotientRight (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) : C →ₗ[K] idealAnnihilator M π →ₗ[K] idealAnnihilator M π :=
  LinearMap.liftOfSurjective (f := LinearMap.ofClass π) hπ
    ⟨(annihilatorModule M π).right.flip, annihilator_right_kernel M π⟩

/-- The descended left action agrees with the original action on a representative. -/
@[simp] theorem quotientLeft_apply (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) (a : A) :
    quotientLeft M π hπ (π a) = (annihilatorModule M π).left a :=
  LinearMap.equivOfSurjective_apply hπ (annihilator_left_kernel M π)

/-- The descended right action agrees with the original action on a representative. -/
@[simp] theorem quotientRight_apply (M : TwoSidedModule K A P) (π : A →ₙₐ[K] C)
    (hπ : Function.Surjective π) (a : A) :
    quotientRight M π hπ (π a) = (annihilatorModule M π).right.flip a :=
  LinearMap.equivOfSurjective_apply hπ (annihilator_right_kernel M π)

/-- **Auxiliary to Theorem 5.1**. The actual quotient-algebra bimodule on the
two-sided annihilator, with both actions descended through the quotient map. -/
noncomputable def quotientAnnihilatorModule (M : TwoSidedModule K A P)
    (π : A →ₙₐ[K] C) (hπ : Function.Surjective π) :
    TwoSidedModule K C (idealAnnihilator M π) where
  left := quotientLeft M π hπ
  right := (quotientRight M π hπ).flip
  left_assoc := by
    intro a b p
    obtain ⟨a, rfl⟩ := hπ a
    obtain ⟨b, rfl⟩ := hπ b
    rw [← map_mul, quotientLeft_apply, quotientLeft_apply, quotientLeft_apply]
    exact (annihilatorModule M π).left_assoc a b p
  right_assoc := by
    intro p a b
    obtain ⟨a, rfl⟩ := hπ a
    obtain ⟨b, rfl⟩ := hπ b
    simp only [LinearMap.flip_apply, ← map_mul, quotientRight_apply]
    exact (annihilatorModule M π).right_assoc p a b
  left_right := by
    intro a p b
    obtain ⟨a, rfl⟩ := hπ a
    obtain ⟨b, rfl⟩ := hπ b
    simp only [LinearMap.flip_apply, quotientLeft_apply, quotientRight_apply]
    exact (annihilatorModule M π).left_right a p b

end Hochschild1945
