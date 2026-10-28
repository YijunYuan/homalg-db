import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Con_bar_map
import HomAlg.Hochschild1945.Aux_Def_2_1_formula
import Mathlib.LinearAlgebra.Multilinear.Curry

/-!
```yaml node
id: "Hochschild1945.Bridge_Def_cochain_mathlib"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Bridge for Def_cochain"
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
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Aux_Def_2_1_formula"
    - "Hochschild1945.Con_bar_map"
decls:
  - "Hochschild1945.cochain_multilinear_equivalence"
  - "Hochschild1945.cochainMultilinearEquiv_apply"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cochain_multilinear_equivalence:
        statement_sha256: "44ad068b99cb85febae39c0dbf0606732a93e79ecc9b15931228b84cc0ee7b57"
        type_hash: "00000000c2dc0fc5"
        meaning_hash: "a750e91f45e5e407"
      Hochschild1945.cochainMultilinearEquiv_apply:
        statement_sha256: "108c72a7be2995ca667cd711aaa6e798b4663b6135b95e6ccac986c93fadcb18"
        type_hash: "0000000057fff57c"
        meaning_hash: "4b4685b409d9d1ea"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Tensor cochains and multilinear maps"
aux:
  parent: "Hochschild1945.Def_cochain"
  kind: "bridge"
  reason: "Prove the actual equivalence between the source tensor-linear maps and Mathlib multilinear
    maps, including evaluation on tuples."
nl_proof_source:
  follows: "agent"
```

## Statement

For every degree $n$, the source space of tensor-linear cochains is linearly equivalent to the space of $n$-multilinear maps in Mathlib. The equivalence preserves evaluation on each tuple of algebra elements.

## Proof

In degree zero, identify a coefficient element with the constant multilinear map on an empty family. In the successor step, curry the final tensor factor using the source bar map, apply the induction hypothesis to the linear-map coefficient space, and uncurry the last multilinear argument. Each step is a linear equivalence. The tuple evaluation formula follows by the same induction. [uses `Hochschild1945.Con_bar_map`] [uses `Hochschild1945.Aux_Def_2_1_formula`]

## Description

Prove the actual equivalence between the source tensor-linear maps and Mathlib multilinear maps, including evaluation on tuples.
-/

namespace Hochschild1945

universe u

variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]

/-- Repeatedly curry actual tensor factors and use Mathlib's inverse right-currying
isomorphism. The base case identifies a zero-cochain with a constant empty-family map. -/
def cochainMultilinearEquiv {Q : Type u} [AddCommGroup Q] [Module K Q] (n : Nat) :
    Cochain K A Q n ≃ₗ[K] MultilinearMap K (fun _ : Fin n => A) Q :=
  match n with
  | 0 => MultilinearMap.constLinearEquivOfIsEmpty (R := K) (S := K)
      (M₁ := fun _ : Fin 0 => A) (M₂ := Q)
  | n + 1 => (barEquiv K A Q n).trans
      ((cochainMultilinearEquiv n).trans
        (multilinearCurryRightEquiv K (fun _ : Fin (n + 1) => A) Q).symm)
termination_by n

/-- The finite function tuple, expressed in the source evaluation's snoc notation. -/
def cochainArgsOfFin : (n : Nat) → (Fin n → A) → CochainArgs A n
  | 0, _ => PUnit.unit
  | n + 1, a => (cochainArgsOfFin n (Fin.init a), a (Fin.last n))

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- The bridge preserves evaluation of the original tensor-linear map on each tuple. -/
theorem cochainMultilinearEquiv_apply {P : Type u} [AddCommGroup P] [Module K P]
    (n : Nat) (f : Cochain K A P n) (a : Fin n → A) :
    cochainMultilinearEquiv n f a = evaluateCochain n f (cochainArgsOfFin n a) := by
  induction n generalizing P with
  | zero => rw [cochainMultilinearEquiv]; rfl
  | succ n ih =>
      rw [cochainMultilinearEquiv]
      change cochainMultilinearEquiv n (barEquiv K A P n f) (Fin.init a) (a (Fin.last n)) = _
      rw [ih]
      rfl

/-- **Bridge for Definition (unnumbered, p. 59, 2)**. The source cochain space
has an actual linear equivalence with Mathlib's multilinear maps in every degree. -/
theorem cochain_multilinear_equivalence {P : Type u} [AddCommGroup P] [Module K P]
    (M : TwoSidedModule K A P) (n : Nat) :
    Nonempty (cochainSpace M n ≃ₗ[K] MultilinearMap K (fun _ : Fin n => A) P) :=
  ⟨cochainMultilinearEquiv n⟩

end Hochschild1945
