import HomAlg.Hochschild1945.Def_two_sided_module
import Mathlib.Algebra.Algebra.NonUnitalHom
import Mathlib.Algebra.Module.Opposite

/-!
```yaml node
id: "Hochschild1945.Bridge_Def_two_sided_module_mathlib"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Bridge for Def_two_sided_module"
  pages:
    - 59
  chapter: "1"
tags:
  - "bridge"
  - "module"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_two_sided_module"
decls:
  - "Hochschild1945.two_sided_module_bridge"
  - "Hochschild1945.twoSidedActionsEquiv"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.two_sided_module_bridge:
        statement_sha256: "42378943bb97c7d7d1ab189f26c678a897811deccd5d79a71e69882eee4a4182"
        type_hash: "00000000c1b44733"
        meaning_hash: "1f174061d61f546d"
      Hochschild1945.twoSidedActionsEquiv:
        statement_sha256: "b6181b290e13ac5fd0d0a6eb72677bb5b746bd96ad0222d01a42e5a4bc6b06b2"
        type_hash: "000000009668267a"
        meaning_hash: "a09efd27e288e2a4"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Two-sided modules and commuting representations"
aux:
  parent: "Hochschild1945.Def_two_sided_module"
  kind: "bridge"
  reason: "Relate the source left/right actions to commuting nonunital algebra representations on the
    linear endomorphism algebra."
nl_proof_source:
  follows: "agent"
```

## Statement

A source two-sided module is equivalent to a pair of commuting nonunital algebra representations of $A$ and its opposite algebra on the linear endomorphism algebra of $P$. The correspondence preserves the actual left and right actions.

## Proof

Send left multiplication to an endomorphism-valued nonunital algebra map. Send right multiplication to such a map on the opposite algebra; reversing multiplication expresses the right-module associativity law. The source compatibility law gives commutation. Conversely, evaluate the two endomorphism representations to recover bilinear actions and all three source laws. Both composites preserve the action maps and are identities. [uses `Hochschild1945.Def_two_sided_module`]

## Description

Relate the source left/right actions to commuting nonunital algebra representations on the linear endomorphism algebra.

## Formalization notes


The `mathlib-bypass-proof` warning matches NonUnitalAlgHom, the representation
type that this bridge explicitly compares with the source's two bilinear actions.
moduleToMathlib and moduleFromMathlib construct both directions, and the inverse
laws recover the actual action maps. No Mathlib cohomology or semisimplicity
result supplies those laws. The source definition and correspondence metadata
are retained; this intentional comparison explains the visible warning.

-/

namespace Hochschild1945

universe u

variable (K A P : Type u) [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- Mathlib's nonunital algebra representations of the algebra and its opposite,
with commuting endomorphisms. The opposite algebra records the order of the right action. -/
structure MathlibTwoSidedActions where
  /-- The Mathlib nonunital representation giving the left action. -/
  left : A →ₙₐ[K] Module.End K P
  /-- The Mathlib nonunital representation giving the right action. -/
  right : Aᵐᵒᵖ →ₙₐ[K] Module.End K P
  /-- The two Mathlib endomorphisms commute, exactly the source compatibility condition. -/
  commute : ∀ a b : A, Commute (left a) (right (MulOpposite.op b))

variable {K A P}

/-- Construct both Mathlib representations from the source's actual bilinear actions. -/
def moduleToMathlib (M : TwoSidedModule K A P) : MathlibTwoSidedActions K A P where
  left :=
    { toFun := M.left
      map_zero' := M.left.map_zero
      map_add' := M.left.map_add
      map_smul' := M.left.map_smul
      map_mul' := fun a b => LinearMap.ext (M.left_assoc a b) }
  right :=
    { toFun := fun a => M.right.flip (MulOpposite.unop a)
      map_zero' := by ext p; simp
      map_add' := by intros; ext p; simp
      map_smul' := by intros; ext p; simp
      map_mul' := by
        intro a b
        ext p
        exact (M.right_assoc p (MulOpposite.unop b) (MulOpposite.unop a)).symm }
  commute a b := LinearMap.ext (fun p => (M.left_right a p b).symm)

/-- Recover the source module by evaluating the two Mathlib endomorphism representations. -/
def moduleFromMathlib (R : MathlibTwoSidedActions K A P) : TwoSidedModule K A P where
  left := LinearMap.ofClass R.left
  right := ((LinearMap.ofClass R.right).comp (MulOpposite.opLinearEquiv K).toLinearMap).flip
  left_assoc a b p := congrArg (fun f : Module.End K P => f p) (map_mul R.left a b)
  right_assoc p a b :=
    (congrArg (fun f : Module.End K P => f p)
      (map_mul R.right (MulOpposite.op b) (MulOpposite.op a))).symm
  left_right a p b := (congrArg (fun f : Module.End K P => f p) (R.commute a b)).symm

/-- Recovering the source module retains its two action maps, not merely its carrier. -/
theorem moduleFromMathlib_toMathlib (M : TwoSidedModule K A P) :
    moduleFromMathlib (moduleToMathlib M) = M := by
  cases M
  rfl

/-- Re-encoding a pair of representations retains both of its nonunital algebra maps. -/
theorem moduleToMathlib_fromMathlib (R : MathlibTwoSidedActions K A P) :
    moduleToMathlib (moduleFromMathlib R) = R := by
  cases R
  rfl

/-- **Bridge for Definition (unnumbered, p. 59, 1)**. A genuine equivalence
between the source module operations and commuting Mathlib nonunital representations.
Using `Module A P` here would incorrectly require an identity and a unital action. -/
def twoSidedActionsEquiv : TwoSidedModule K A P ≃ MathlibTwoSidedActions K A P where
  toFun := moduleToMathlib
  invFun := moduleFromMathlib
  left_inv := moduleFromMathlib_toMathlib
  right_inv := moduleToMathlib_fromMathlib

/-- **Bridge for Definition (unnumbered, p. 59, 1)**. Both encodings agree,
as witnessed by the action-preserving maps proved above. -/
theorem two_sided_module_bridge :
    Nonempty (TwoSidedModule K A P ≃ MathlibTwoSidedActions K A P) := ⟨twoSidedActionsEquiv⟩

end Hochschild1945
