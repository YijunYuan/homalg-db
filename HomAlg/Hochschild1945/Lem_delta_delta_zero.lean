import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Prop_1_1
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_bar_map

/-!
```yaml node
id: "Hochschild1945.Lem_delta_delta_zero"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Lemma (unnumbered, p. 60, 1)"
  pages:
    - 60
  chapter: "2"
tags:
  - "cochain-complex"
  - "cohomology"
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
  - "Hochschild1945.delta_delta_zero"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.delta_delta_zero:
        statement_sha256: "4d89cb2ad1663dc5723320f37d1a2797fbe795d102e6fb01b39e5142debaf42a"
        type_hash: "0000000038aacc91"
        meaning_hash: "10224928595776d9"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "The coboundary squares to zero"
```

## Statement

We wish to prove that $\delta\delta f=0$, for every cochain $f$.

## Proof

We shall do this
by making an induction on the dimension $m$ of $f$: For $m=0$, $f\in\mathfrak{P}$,
and $\delta f\{a\}=a\cdot f-f\cdot a$,
\[
\begin{aligned}
\delta\delta f\{a_1,a_2\}
&=a_1\cdot\delta f\{a_2\}-\delta f\{a_1a_2\}+\delta f\{a_1\}\cdot a_2\\
&=a_1\cdot(a_2\cdot f-f\cdot a_2)-(a_1a_2\cdot f-f\cdot a_1a_2)
 +(a_1\cdot f-f\cdot a_1)\cdot a_2\\
&=0.
\end{aligned}
\]
Corresponding to any element $f$ of $(\mathfrak{A}^{(m)}:\mathfrak{P})$, $m\geqq 1$, we define
an element $\bar f\in(\mathfrak{A}^{(m-1)}:(\mathfrak{A}:\mathfrak{P}))$ by the relation
$\bar f\{a_1,\cdots,a_{m-1}\}\{a_m\}=f\{a_1,\cdots,a_m\}$.
(We identify $(\mathfrak{A}^{(0)}:(\mathfrak{A}:\mathfrak{P}))$ with $(\mathfrak{A}:\mathfrak{P})$). Then we can verify
directly from Definition 2.1 that, if $f\in(\mathfrak{A}^{(m)}:\mathfrak{P})$, $m\geqq 1$,
\[
\begin{aligned}
\delta f\{a_1,\cdots,a_{m+1}\}
&=(a_1*\bar f\{a_2,\cdots,a_m\})\{a_{m+1}\}\\
&\quad+\sum_{i=1}^{m-1}(-1)^i\bar f\{a_1,\cdots,a_i a_{i+1},\cdots,a_m\}\{a_{m+1}\}\\
&\quad+(-1)^m(\bar f\{a_1,\cdots,a_{m-1}\}*a_m)\{a_{m+1}\}\\
&=\delta\bar f\{a_1,\cdots,a_m\}\{a_{m+1}\},\quad\hbox{whence}\quad
\overline{\delta f}=\delta\bar f.
\end{aligned}
\]
Thus, $\overline{\delta\delta f}=\delta\overline{\delta f}=\delta\delta\bar f$.

Since $\dim(\bar f)=\dim(f)-1$, and since $\bar f=0$ only if $f=0$, we can
now apply induction to prove our result.

[uses `Hochschild1945.Con_bar_map`] [uses `Hochschild1945.Prop_1_1`]

## Description

Consecutive source coboundaries vanish by the printed degree-zero calculation and currying induction.
-/

namespace Hochschild1945

universe u

variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]

/-- **Lemma (unnumbered, p. 60, 1)**. Consecutive coboundaries vanish.
The proof follows the printed induction: expand the three terms in degree zero,
then curry the last tensor factor and apply the result to the special coefficient module. -/
theorem delta_delta_zero {P : Type u} [AddCommGroup P] [Module K P]
    (M : TwoSidedModule K A P) (n : Nat) (f : Cochain K A P n) :
    delta M (n + 1) (delta M n f) = 0 := by
  induction n generalizing P with
  | zero =>
      apply (barEquiv K A P 1).injective
      ext a b
      change delta M 1 (delta M 0 f) (TensorProduct.tmul K a b) = 0
      rw [delta_one_apply]
      simp only [delta]
      change M.left a (M.left b f - M.right f b) -
          (M.left (a * b) f - M.right f (a * b)) +
          M.right (M.left a f - M.right f a) b = 0
      simp only [map_sub, LinearMap.sub_apply, M.left_assoc, M.right_assoc, M.left_right]
      abel
  | succ n ih =>
      apply (barEquiv K A P (n + 2)).injective
      rw [bar_delta, bar_delta, map_zero]
      exact ih (twistedModule M) (barEquiv K A P n f)

end Hochschild1945
