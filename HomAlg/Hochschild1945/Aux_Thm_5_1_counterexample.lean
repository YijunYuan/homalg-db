import HomAlg.Hochschild1945.Aux_Def_2_1_formula
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Lem_delta_delta_zero
import Mathlib.Data.Rat.Defs
import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

/-!
```yaml node
id: "Hochschild1945.Aux_Thm_5_1_counterexample"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Counterexample to Theorem 5.1"
  pages:
    - 63
    - 64
  chapter: "5"
tags:
  - "hochschild-cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Lem_delta_delta_zero"
    - "Hochschild1945.Aux_Def_2_1_formula"
decls:
  - "Hochschild1945.Counterexample5.primitive_dependence"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Counterexample5.primitive_dependence:
        statement_sha256: "9139a41e8109f300edf6631ade800ca930795e196b03efa17910043bb5735cfc"
        type_hash: "00000000218db5a8"
        meaning_hash: "e5ed88f303240757"
    session: "root-counterexample-independent"
    author_session: "/root/lean_fixtures"
title: "Failure of primitive independence in Theorem 5.1"
aux:
  parent: "Hochschild1945.Thm_5_1"
  kind: "lemma"
  reason: "Exhibit actual source actions and a coboundary which vanishes on the ideal but has no primitive
    in its two-sided annihilator."
nl_proof_source:
  follows: "agent"
```

## Statement

Over the zero-product rational algebra with basis $a,b$, take $P=\mathbb Q^2$ and $T(x,y)=(y,0)$. Set $L_a=L_b=R_b=T$ and $R_a=0$. The source coboundary of $(0,1)$ vanishes on the ideal spanned by $b$, but is not the coboundary of any element annihilated on both sides by that ideal.

## Proof

The identity $T^2=0$ proves all three bimodule laws. The source degree-zero differential sends $q$ to the map $(r,s)\mapsto(rq_2,0)$. Thus the displayed coboundary is a cocycle by $\delta^2=0$, vanishes on the ideal, and has value $(1,0)$ at $a$. An annihilated primitive has second coordinate zero, so its coboundary has value zero at $a$, a contradiction. [uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Lem_delta_delta_zero`]

[uses `Hochschild1945.Aux_Def_2_1_formula`]

## Description

A concrete finite-dimensional witness to the choice-of-primitive gap in the printed proof. The full cohomology calculation is recorded in the associated review report. The source theorem remains disputed, not corrected or approved.
-/

namespace Hochschild1945

namespace Counterexample5

/-- The two-dimensional rational vector space, with zero multiplication. -/
def Algebra := ℚ × ℚ

/-- The rational plane additive group, scoped to this counterexample. -/
local instance : AddCommGroup Algebra := inferInstanceAs (AddCommGroup (ℚ × ℚ))
/-- Coordinate-wise rational scalar multiplication. -/
local instance : Module ℚ Algebra := inferInstanceAs (Module ℚ (ℚ × ℚ))
/-- The underlying vector space has dimension two. -/
local instance : FiniteDimensional ℚ Algebra :=
  inferInstanceAs (FiniteDimensional ℚ (ℚ × ℚ))

/-- The product of every pair is zero; associativity and distributivity follow. -/
local instance : NonUnitalRing Algebra where
  mul _ _ := 0
  mul_assoc _ _ _ := rfl
  left_distrib _ _ _ := (add_zero 0).symm
  right_distrib _ _ _ := (add_zero 0).symm
  zero_mul _ := rfl
  mul_zero _ := rfl

/-- The zero product is linear in its right argument. -/
local instance : SMulCommClass ℚ Algebra Algebra where
  smul_comm _ _ _ := smul_zero _

/-- The zero product is linear in its left argument. -/
local instance : IsScalarTower ℚ Algebra Algebra where
  smul_assoc _ _ _ := (smul_zero _).symm

/-- The first coordinate of a sum. -/
@[simp] theorem add_first (x y : Algebra) : (x + y).1 = x.1 + y.1 := rfl
/-- The second coordinate of a sum. -/
@[simp] theorem add_second (x y : Algebra) : (x + y).2 = x.2 + y.2 := rfl
/-- The first coordinate of a scalar multiple. -/
@[simp] theorem smul_first (r : ℚ) (x : Algebra) : (r • x).1 = r * x.1 := rfl
/-- The second coordinate of a scalar multiple. -/
@[simp] theorem smul_second (r : ℚ) (x : Algebra) : (r • x).2 = r * x.2 := rfl
/-- Multiplication in the example vanishes identically. -/
@[simp] theorem mul_eq_zero (x y : Algebra) : x * y = 0 := rfl
/-- The first coordinate of zero. -/
@[simp] theorem zero_first : (0 : Algebra).1 = 0 := rfl
/-- The second coordinate of zero. -/
@[simp] theorem zero_second : (0 : Algebra).2 = 0 := rfl

/-- The nilpotent operator used in both actions. -/
def shift : (ℚ × ℚ) →ₗ[ℚ] (ℚ × ℚ) where
  toFun p := (p.2, 0)
  map_add' _ _ := by simp
  map_smul' _ _ := by simp

/-- The coefficient module with left(a)=left(b)=T and right(a)=0, right(b)=T. -/
def coefficientModule : TwoSidedModule ℚ Algebra (ℚ × ℚ) where
  left :=
    { toFun := fun x => (x.1 + x.2) • shift
      map_add' := by intros; ext <;> simp [shift] <;> ring
      map_smul' := by intros; ext <;> simp [shift] <;> ring }
  right :=
    { toFun := fun p =>
        { toFun := fun x => x.2 • shift p
          map_add' := by intros; simp [add_smul]
          map_smul' := by intros; simp [mul_smul] }
      map_add' := by intros; ext <;> simp [shift, mul_add]
      map_smul' := by intros; ext <;> simp [shift] <;> ring }
  left_assoc := by intros; simp [shift]; rfl
  right_assoc := by intros; simp [shift]
  left_right := by intros; simp [shift]

/-- The distinguished algebra generators and coefficient primitive. -/
def first : Algebra := (1, 0)
/-- The generator of the ideal under consideration. -/
def second : Algebra := (0, 1)
/-- A correcting primitive which centralizes but does not annihilate the ideal. -/
def primitive : ℚ × ℚ := (0, 1)

/-- An actual source coboundary, not a replacement model of the differential. -/
def witness : Cochain ℚ Algebra (ℚ × ℚ) 1 := delta coefficientModule 0 primitive

/-- Evaluating the source differential gives (x.first,0). -/
theorem witness_apply (x : Algebra) : witness x = (x.1, 0) := by
  rw [witness, delta_zero_apply]
  simp [coefficientModule, primitive, shift]

/-- **Auxiliary to Theorem 5.1** (Contributor). The same zero cohomology class has a
representative vanishing on the ideal span(second), but that representative is
not a coboundary of an element annihilated by the ideal. This disproves the
printed assertion that the quotient cocycle is independent of the choice of
primitive. Compute the two actions using T²=0 and use the source δ²=0 theorem. -/
theorem primitive_dependence :
    IsCoboundary coefficientModule 0 witness ∧
    IsCocycle coefficientModule 1 witness ∧
    (∀ t : ℚ, witness (0, t) = 0) ∧
    ¬ ∃ q : ℚ × ℚ,
      (∀ t : ℚ, coefficientModule.left (0, t) q = 0 ∧
        coefficientModule.right q (0, t) = 0) ∧
      witness = delta coefficientModule 0 q := by
  refine ⟨⟨primitive, rfl⟩, delta_delta_zero coefficientModule 0 primitive, ?_, ?_⟩
  · intro t
    exact witness_apply (0, t)
  · rintro ⟨q, hq, heq⟩
    have hy : q.2 = 0 := by
      have h := congrArg Prod.fst (hq 1).1
      simpa [coefficientModule, shift] using h
    have h := congrArg (fun f : Cochain ℚ Algebra (ℚ × ℚ) 1 => (f first).1) heq
    rw [witness_apply, delta_zero_apply] at h
    change 1 = (1 + 0) * q.2 - 0 * q.2 at h
    norm_num [hy] at h

end Counterexample5

end Hochschild1945
