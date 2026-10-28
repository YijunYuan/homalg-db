import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_bar_map
import HomAlg.Hochschild1945.Prop_1_1
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.Abel

/-!
```yaml node
id: "Hochschild1945.Aux_Def_2_1_formula"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Auxiliary to Definition 2.1"
  pages:
    - 59
    - 60
  chapter: "2"
tags:
  - "cohomology"
  - "technical"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Con_bar_map"
    - "Hochschild1945.Prop_1_1"
decls:
  - "Hochschild1945.delta_evaluate_formula"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.delta_evaluate_formula:
        statement_sha256: "88b2e0d4de74474dc2681cb19c8770926a83f49f3b6e0f19e5df33d48c0d2a65"
        type_hash: "00000000a77994f1"
        meaning_hash: "cd4876aca7511df4"
    session: "root-sections123-independent"
    author_session: "/root/ci_governance"
aux:
  parent: "Hochschild1945.Def_2_1"
  kind: "technical"
  reason: "Connect the recursive currying implementation of the coboundary to its printed alternating-sum
    formula."
nl_proof_source:
  follows: "agent"
```

## Statement

$\delta$ maps $(\mathfrak{A}^{(m)}:\mathfrak{P})$ linearly into $(\mathfrak{A}^{(m+1)}:\mathfrak{P})$. If
$f\in(\mathfrak{A}^{(m)}:\mathfrak{P})$,
\[
\begin{aligned}
\delta f\{a_1,\cdots,a_{m+1}\}
&=a_1\cdot f\{a_2,\cdots,a_{m+1}\}\\
&\quad+\sum_{i=1}^{m}(-1)^i f\{a_1,\cdots,a_i a_{i+1},\cdots,a_{m+1}\}\\
&\quad+(-1)^{m+1}f\{a_1,\cdots,a_m\}\cdot a_{m+1}.
\end{aligned}
\]

## Proof

Induct on the degree. The degree-zero formula is the defining difference of the two actions. Curry the last tensor factor using the source bar map. [uses `Hochschild1945.Con_bar_map`] Apply the induction hypothesis with the twisted one-cochain module. Its right action splits into evaluation on the product of the last two arguments minus the original right action. [uses `Hochschild1945.Prop_1_1`] Split the finite sum at its final index and use the next alternating sign.

## Description

Verifies the displayed alternating-sum formula for the recursive tensor implementation of the source coboundary. Tuple evaluation is related explicitly to the original linear map on pure tensors.
-/

namespace Hochschild1945

open scoped BigOperators TensorProduct

universe u

/-- A finite tuple stored by repeatedly appending its last argument. -/
@[reducible] def CochainArgs (A : Type u) : Nat → Type u
  | 0 => PUnit
  | n + 1 => CochainArgs A n × A

/-- The first argument of a nonempty tuple. -/
def CochainArgs.head {A : Type u} : {n : Nat} → CochainArgs A (n + 1) → A
  | 0, a => a.2
  | _n + 1, a => head a.1

/-- Delete the first argument of a nonempty tuple. -/
def CochainArgs.tail {A : Type u} : {n : Nat} → CochainArgs A (n + 1) → CochainArgs A n
  | 0, _ => PUnit.unit
  | _n + 1, a => (tail a.1, a.2)

/-- Multiply adjacent arguments at the indicated zero-based position. -/
def CochainArgs.merge {A : Type u} [Mul A] :
    (n : Nat) → CochainArgs A (n + 1) → Fin n → CochainArgs A n
  | 0, _, i => Fin.elim0 i
  | n + 1, a, i => Fin.lastCases (a.1.1, a.1.2 * a.2)
      (fun j => (merge n a.1 j, a.2)) i

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- Evaluation on a tuple by currying the final tensor factor. Degree zero
is the coefficient element itself, precisely as in the source. -/
def evaluateCochain {Q : Type u} [AddCommGroup Q] [Module K Q] :
    (n : Nat) → Cochain K A Q n → CochainArgs A n → Q
  | 0, f, _ => f
  | n + 1, f, a => evaluateCochain n (barEquiv K A Q n f) a.1 a.2

/-- The pure tensor attached to a positive-length tuple. -/
def cochainPureTensor : (n : Nat) → CochainArgs A (n + 1) → KroneckerPower K A n
  | 0, a => a.2
  | n + 1, a => cochainPureTensor n a.1 ⊗ₜ[K] a.2

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- Iterated currying evaluates the original linear map on the source's
Kronecker product of the arguments. -/
theorem evaluateCochain_pureTensor (n : Nat) (f : Cochain K A P (n + 1))
    (a : CochainArgs A (n + 1)) :
    evaluateCochain (K := K) (A := A) (n + 1) f a = f (cochainPureTensor n a) := by
  induction n generalizing P with
  | zero => rfl
  | succ n ih =>
    change (evaluateCochain (n + 1) (barEquiv K A P (n + 1) f) a.1) a.2 =
      f (cochainPureTensor n a.1 ⊗ₜ[K] a.2)
    rw [ih]
    rfl

/-- **Auxiliary to Definition 2.1**. The recursively curried coboundary has
the printed alternating-sum formula on every tuple of algebra elements. The
finite sum uses zero-based positions, hence the exponent `i.val + 1`. -/
theorem delta_evaluate_formula (n : Nat) (M : TwoSidedModule K A P)
    (f : Cochain K A P n) (a : CochainArgs A (n + 1)) :
    evaluateCochain (K := K) (A := A) (n + 1) (delta M n f) a =
      M.left a.head (evaluateCochain n f a.tail) +
      (∑ i : Fin n, (-1 : ℤ) ^ (i.val + 1) •
        evaluateCochain n f (CochainArgs.merge n a i)) +
      (-1 : ℤ) ^ (n + 1) • M.right (evaluateCochain n f a.1) a.2 := by
  induction n generalizing P with
  | zero =>
    change delta M 0 f a.2 = M.left a.2 f +
      (∑ i : Fin 0, (-1 : ℤ) ^ (i.val + 1) •
        evaluateCochain 0 f (CochainArgs.merge 0 a i)) +
      (-1 : ℤ) ^ 1 • M.right f a.2
    calc
      delta M 0 f a.2 = M.left a.2 f - M.right f a.2 := delta_zero_apply M f a.2
      _ = _ := by simp [sub_eq_add_neg]
  | succ n ih =>
    change (evaluateCochain (n + 1)
      (barEquiv K A P (n + 1) (delta M (n + 1) f)) a.1) a.2 = _
    rw [bar_delta, ih]
    simp only [LinearMap.add_apply, LinearMap.sum_apply, LinearMap.smul_apply,
      twistedModule, homLeft_apply, homRight_apply]
    rw [Fin.sum_univ_castSucc]
    simp only [evaluateCochain, Fin.val_castSucc, Fin.val_last, CochainArgs.merge,
      Fin.lastCases_castSucc, Fin.lastCases_last, CochainArgs.head, CochainArgs.tail]
    simp only [pow_succ, mul_neg_one, neg_smul, smul_sub]
    abel

end Hochschild1945
