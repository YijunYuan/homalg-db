import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Bridge_Def_cochain_mathlib
import HomAlg.Hochschild1945.Aux_Def_2_1_formula
import Mathlib.Algebra.Algebra.NonUnitalSubalgebra
import Mathlib.LinearAlgebra.FiniteDimensional.Basic

/-!
```yaml node
id: "Hochschild1945.Def_natural_homomorphism"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 63)"
  pages:
    - 63
  chapter: "5"
tags:
  - "hochschild-cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_2_2"
  proof:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Bridge_Def_cochain_mathlib"
    - "Hochschild1945.Aux_Def_2_1_formula"
decls:
  - "Hochschild1945.naturalHomomorphism"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.naturalHomomorphism:
        statement_sha256: "347b8c6c7cbdf8f53d191c73d9063295963ef0adbf7ed503f6f67ef9cf50765a"
        type_hash: "00000000b55ccc78"
        meaning_hash: "7bd399a8f2673ed4"
    session: "ci-section5-independent"
    author_session: "/root/lean_fixtures"
title: "Natural restriction homomorphism"
```

## Statement

If $\mathfrak{B}$ is an ideal of the algebra $\mathfrak{A}$ and $\mathfrak{P}$ a two-sided $\mathfrak{A}$-module, then $\mathfrak{P}$ is also a two-sided $\mathfrak{B}$-module. A $\mathfrak{P}$-cochain $f$ of $\mathfrak{A}$, when restricted to $\mathfrak{B}$, determines a $\mathfrak{P}$-cochain $\hat f$ of $\mathfrak{B}$. The mapping $f\to\hat f$ is clearly linear and maps cocycles into cocycles, and coboundaries into coboundaries. Therefore, it defines a homomorphism of $H^m(\mathfrak{A},\mathfrak{P})$ into $H^m(\mathfrak{B},\mathfrak{P})$ which we shall call the natural homomorphism.

## Description

Defines the natural map on cohomology by restricting cochains to an ideal.
## Formalization notes

The principal definition takes an actual scalar-closed two-sided ideal. General pullback along an algebra homomorphism is only a helper. Cochains remain the source tensor-linear maps: the proved multilinear bridge constructs argument restriction, and its evaluation identity plus the printed alternating-sum formula proves commutation with the source differential in every degree. The final map is the induced linear map of the actual cocycle/boundary quotients.
-/

namespace Hochschild1945

universe u

variable {K A B P : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]
  [FiniteDimensional K B]
  [AddCommGroup P] [Module K P]

/-- Restrict both source actions along an actual nonunital algebra homomorphism. -/
def restrictModule (M : TwoSidedModule K A P) (φ : B →ₙₐ[K] A) :
    TwoSidedModule K B P where
  left := M.left.comp (LinearMap.ofClass φ)
  right :=
    { toFun := fun p => (M.right p).comp (LinearMap.ofClass φ)
      map_add' := by intros; ext; simp
      map_smul' := by intros; ext; simp }
  left_assoc := by intro a b p; simpa using M.left_assoc (φ a) (φ b) p
  right_assoc := by intro p a b; simpa using M.right_assoc p (φ a) (φ b)
  left_right := by intro a p b; exact M.left_right (φ a) p (φ b)

/-- Restrict actual tensor-linear cochains by precomposing every multilinear
argument through the proved tensor/multilinear equivalence. -/
def restrictCochain (φ : B →ₙₐ[K] A) (n : Nat) :
    Cochain K A P n →ₗ[K] Cochain K B P n :=
  (cochainMultilinearEquiv (K := K) (A := B) n).symm.toLinearMap ∘ₗ
    (MultilinearMap.compLinearMapₗ (fun _ : Fin n => LinearMap.ofClass φ)) ∘ₗ
    (cochainMultilinearEquiv (K := K) (A := A) n).toLinearMap

/-- Map each argument of a source tuple. -/
def CochainArgs.map {X Y : Type u} (f : X → Y) :
    (n : Nat) → CochainArgs X n → CochainArgs Y n
  | 0, _ => PUnit.unit
  | n + 1, a => (CochainArgs.map f n a.1, f a.2)

/-- Every source tuple is the snoc presentation of a finite function tuple. -/
theorem cochainArgsOfFin_surjective {X : Type u} (n : Nat) :
    Function.Surjective (cochainArgsOfFin (A := X) n) := by
  induction n with
  | zero => intro a; exact ⟨Fin.elim0, Subsingleton.elim _ _⟩
  | succ n ih =>
      rintro ⟨a, x⟩
      obtain ⟨v, rfl⟩ := ih a
      refine ⟨Fin.snoc v x, ?_⟩
      simp [cochainArgsOfFin]

/-- Mapping arguments commutes with the bridge's tuple representation. -/
theorem CochainArgs.map_ofFin {X Y : Type u} (f : X → Y) (n : Nat) (a : Fin n → X) :
    CochainArgs.map f n (cochainArgsOfFin n a) =
      cochainArgsOfFin n (fun i => f (a i)) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      change (CochainArgs.map f n (cochainArgsOfFin n (Fin.init a)), f (a (Fin.last n))) = _
      rw [ih]
      rfl

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- Tuple evaluation detects equality of tensor-linear cochains. -/
theorem cochain_ext (n : Nat) (f g : Cochain K A P n)
    (h : ∀ a, evaluateCochain n f a = evaluateCochain n g a) : f = g := by
  apply (cochainMultilinearEquiv (K := K) (A := A) n).injective
  ext a
  simpa only [cochainMultilinearEquiv_apply] using h (cochainArgsOfFin n a)

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [SMulCommClass K B B] [IsScalarTower K B B] [FiniteDimensional K B] in
/-- Restriction evaluates the original cochain on the mapped tuple. -/
theorem restrictCochain_evaluate (φ : B →ₙₐ[K] A) (n : Nat)
    (f : Cochain K A P n) (a : CochainArgs B n) :
    evaluateCochain n (restrictCochain φ n f) a =
      evaluateCochain n f (CochainArgs.map φ n a) := by
  obtain ⟨v, rfl⟩ := cochainArgsOfFin_surjective n a
  rw [CochainArgs.map_ofFin, ← cochainMultilinearEquiv_apply,
    ← cochainMultilinearEquiv_apply]
  simp [restrictCochain]

/-- Mapping a nonempty tuple preserves its first argument. -/
theorem CochainArgs.map_head {X Y : Type u} (f : X → Y) (n : Nat)
    (a : CochainArgs X (n + 1)) : (CochainArgs.map f (n + 1) a).head = f a.head := by
  induction n with
  | zero => rfl
  | succ n ih => exact ih a.1

/-- Mapping commutes with deleting the first argument. -/
theorem CochainArgs.map_tail {X Y : Type u} (f : X → Y) (n : Nat)
    (a : CochainArgs X (n + 1)) :
    (CochainArgs.map f (n + 1) a).tail = CochainArgs.map f n a.tail := by
  induction n with
  | zero => rfl
  | succ n ih => exact congrArg (fun t => (t, f a.2)) (ih a.1)

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [SMulCommClass K B B] [IsScalarTower K B B] [FiniteDimensional K B] in
/-- A multiplicative map commutes with merging adjacent arguments. -/
theorem CochainArgs.map_merge (φ : B →ₙₐ[K] A) (n : Nat)
    (a : CochainArgs B (n + 1)) (i : Fin n) :
    CochainArgs.merge n (CochainArgs.map φ (n + 1) a) i =
      CochainArgs.map φ n (CochainArgs.merge n a i) := by
  induction n with
  | zero => exact Fin.elim0 i
  | succ n ih =>
      induction i using Fin.lastCases with
      | last => simp [CochainArgs.merge, CochainArgs.map]
      | cast j =>
          simp only [CochainArgs.merge, Fin.lastCases_castSucc, CochainArgs.map]
          exact congrArg (fun t => (t, φ a.2)) (ih a.1 j)

/-- **Auxiliary to Definition (unnumbered, p. 63)**. Restriction commutes with
δ. Evaluate both sides on a tuple and use the source alternating-sum formula:
φ respects products and each restricted endpoint action is the original action
of φ(b). Tensor pure products span, so the cochains agree. -/
theorem restrictCochain_delta (M : TwoSidedModule K A P) (φ : B →ₙₐ[K] A)
    (n : Nat) (f : Cochain K A P n) :
    restrictCochain φ (n + 1) (delta M n f) =
      delta (restrictModule M φ) n (restrictCochain φ n f)  := by
  apply cochain_ext
  intro a
  rw [restrictCochain_evaluate, delta_evaluate_formula, delta_evaluate_formula]
  simp only [restrictCochain_evaluate, CochainArgs.map_head, CochainArgs.map_tail,
    CochainArgs.map_merge]
  rfl


/-- Restriction of a cocycle is a cocycle by the proved cochain identity. -/
def restrictCocycles (M : TwoSidedModule K A P) (φ : B →ₙₐ[K] A) (n : Nat) :
    cocycles M n →ₗ[K] cocycles (restrictModule M φ) n :=
  ((restrictCochain φ n).comp (cocycles M n).subtype).codRestrict
    (cocycles (restrictModule M φ) n) (by
      intro f
      change delta (restrictModule M φ) n (restrictCochain φ n f) = 0
      rw [← restrictCochain_delta, (f.property : delta M n f = 0), map_zero])

/-- Restriction sends a boundary primitive to its restriction. -/
theorem restrict_boundaries (M : TwoSidedModule K A P) (φ : B →ₙₐ[K] A)
    (n : Nat) :
    boundariesInCycles M n ≤
      (boundariesInCycles (restrictModule M φ) n).comap (restrictCocycles M φ n) := by
  intro f hf
  rw [mem_boundariesInCycles] at hf
  change restrictCocycles M φ n f ∈ boundariesInCycles (restrictModule M φ) n
  rw [mem_boundariesInCycles]
  cases n with
  | zero =>
      have h : (f : Cochain K A P 0) = 0 := hf
      change (restrictCochain φ 0 (f : Cochain K A P 0)) ∈ (⊥ : Submodule K (Cochain K B P 0))
      rw [Submodule.mem_bot]
      rw [h, map_zero]
  | succ n =>
      obtain ⟨g, hg⟩ := hf
      refine ⟨restrictCochain φ n g, ?_⟩
      change delta (restrictModule M φ) n (restrictCochain φ n g) =
        restrictCochain φ (n + 1) f
      rw [← restrictCochain_delta, hg]

/-- **Definition (unnumbered, p. 63)** (Hochschild). The natural homomorphism is
the actual map of cocycle quotients induced by restriction. Apply this to the
inclusion of an ideal; the construction also works for any algebra homomorphism. -/
def cohomologyPullback (M : TwoSidedModule K A P) (φ : B →ₙₐ[K] A) (n : Nat) :
    Cohomology M n →ₗ[K] Cohomology (restrictModule M φ) n :=
  (boundariesInCycles M n).mapQ (boundariesInCycles (restrictModule M φ) n)
    (restrictCocycles M φ n) (restrict_boundaries M φ n)

/-- A scalar-closed two-sided ideal in the source nonunital algebra. -/
structure AlgebraIdeal (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] where
  /-- The scalar-closed multiplicative subspace. -/
  subalgebra : NonUnitalSubalgebra K A
  /-- The ideal absorbs multiplication on the left. -/
  mul_mem_left : ∀ a b : A, b ∈ subalgebra → a * b ∈ subalgebra
  /-- The ideal absorbs multiplication on the right. -/
  mul_mem_right : ∀ a b : A, b ∈ subalgebra → b * a ∈ subalgebra

/-- An ideal of the finite source algebra is finite dimensional. -/
theorem idealFiniteDimensional (I : AlgebraIdeal K A) : FiniteDimensional K I.subalgebra :=
  FiniteDimensional.of_injective
    (LinearMap.ofClass (NonUnitalSubalgebraClass.subtype I.subalgebra)) Subtype.coe_injective

attribute [local instance] idealFiniteDimensional

/-- **Definition (unnumbered, p. 63)** (Hochschild). Restrict actual tensor-linear
cochains to the ideal and pass to the actual source cocycle/boundary quotients. -/
def naturalHomomorphism (M : TwoSidedModule K A P) (I : AlgebraIdeal K A) (n : Nat) :
    Cohomology M n →ₗ[K]
      Cohomology (restrictModule M (NonUnitalSubalgebraClass.subtype I.subalgebra)) n :=
  cohomologyPullback M (NonUnitalSubalgebraClass.subtype I.subalgebra) n

end Hochschild1945
