import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Con_bar_map
import HomAlg.Hochschild1945.Prop_1_1

/-!
```yaml node
id: "Hochschild1945.Def_2_1"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition 2.1"
  pages:
    - 59
  chapter: "2"
tags:
  - "cochain-complex"
  - "cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Con_bar_map"
    - "Hochschild1945.Prop_1_1"
decls:
  - "Hochschild1945.delta"
  - "Hochschild1945.deltaZero"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.delta:
        statement_sha256: "90719edc80ff25e4465c2b0fbb800688d910b679a48bccedd1eadd1543f0b0ef"
        type_hash: "000000004656e0f8"
        meaning_hash: "87168462703fbff6"
      Hochschild1945.deltaZero:
        statement_sha256: "cabde4acaa24e24df1280dd81ad74d70fd1c936766bb858d2d98020d312a8a3a"
        type_hash: "00000000bef92092"
        meaning_hash: "598347b0e817abb1"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Coboundary operator"
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

## Description

The source coboundary operator on tensor-linear cochains, with its actual alternating signs and action order.
## Formalization notes

The implementation uses the last-factor currying recurrence proved on printed
page 60. `Aux_Def_2_1_formula.delta_evaluate_formula` independently proves that
this recurrence has exactly Definition 2.1's displayed alternating-sum formula
in every degree; its pure-tensor evaluation lemma identifies the arguments with
the original tensor-linear maps. Thus the recurrence does not assume a new
operator or replace the source definition with an unrelated chain complex.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- The degree-zero instance of the printed coboundary, `δp(a) = a·p - p·a`. -/
def deltaZero (M : TwoSidedModule K A P) : P →ₗ[K] (A →ₗ[K] P) :=
  LinearMap.mk₂ K (fun p a => M.left a p - M.right p a)
    (by intros; simp; abel)
    (by intros; simp [smul_sub])
    (by intros; simp; abel)
    (by intros; simp [smul_sub])

/-- **Definition 2.1**. The source coboundary is implemented through its proved
last-factor currying recurrence from p. 60. It starts with the printed degree-zero
formula and uses exactly the special module of Proposition 1.1 at each step. -/
def delta {Q : Type u} [AddCommGroup Q] [Module K Q]
    (M : TwoSidedModule K A Q) (n : Nat) :
    Cochain K A Q n →ₗ[K] Cochain K A Q (n + 1) :=
  match n with
  | 0 => deltaZero M
  | n + 1 => (barEquiv K A Q (n + 1)).symm.toLinearMap ∘ₗ
      delta (twistedModule M) n ∘ₗ (barEquiv K A Q n).toLinearMap
termination_by n

/-- The coboundary and source bar map commute, as in the displayed p. 60 identity. -/
@[simp] theorem bar_delta (M : TwoSidedModule K A P) (n : Nat)
    (f : Cochain K A P (n + 1)) :
    barEquiv K A P (n + 1) (delta M (n + 1) f) =
      delta (twistedModule M) n (barEquiv K A P n f) := by
  simp only [delta, LinearMap.comp_apply, LinearEquiv.coe_coe,
    LinearEquiv.apply_symm_apply]

/-- The displayed formula in degree zero is definitionally the original one. -/
@[simp] theorem delta_zero_apply (M : TwoSidedModule K A P) (p : P) (a : A) :
    delta M 0 p a = M.left a p - M.right p a := by
  simp only [delta]
  rfl

/-- The degree-one coboundary expands to the three terms used in the source's base case. -/
theorem delta_one_apply (M : TwoSidedModule K A P) (f : Cochain K A P 1) (a b : A) :
    delta M 1 f (TensorProduct.tmul K a b) =
      M.left a (f b) - f (a * b) + M.right (f a) b := by
  rw [delta, delta]
  change M.left a (f b) - (f (a * b) - M.right (f a) b) = _
  abel

end Hochschild1945
