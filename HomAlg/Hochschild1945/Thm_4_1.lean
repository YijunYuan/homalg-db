import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Cited_simple_inseparable_center
import HomAlg.Hochschild1945.Cited_semisimple_representations
import HomAlg.Hochschild1945.Cited_separable_splitting
import HomAlg.Hochschild1945.Cited_separable_identity
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Lem_4_1
import Mathlib.Data.Matrix.Basis
import Mathlib.LinearAlgebra.Matrix.FiniteDimensional
import Mathlib.Tactic.Abel
import Mathlib.Algebra.BigOperators.Group.Finset.Sigma
import Mathlib.RingTheory.TensorProduct.Basic
import Mathlib.LinearAlgebra.TensorProduct.Lift
import Mathlib.LinearAlgebra.TensorProduct.Basis
import Mathlib.LinearAlgebra.TensorProduct.Tower
import Mathlib.LinearAlgebra.Dual.Lemmas
import Mathlib.LinearAlgebra.Basis.VectorSpace
import HomAlg.Hochschild1945.Def_natural_homomorphism
import Mathlib.Algebra.Algebra.NonUnitalHom
import Mathlib.LinearAlgebra.Projection
import Mathlib.LinearAlgebra.Matrix.ToLin
import HomAlg.Hochschild1945.Cited_inseparable_simple_component
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Def_2_2

/-!
```yaml node
id: "Hochschild1945.Thm_4_1"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Theorem 4.1"
  pages:
    - 61
    - 62
    - 63
  chapter: "4"
tags:
  - "hochschild-cohomology"
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Lem_4_1"
    - "Hochschild1945.Cited_separable_identity"
    - "Hochschild1945.Cited_separable_splitting"
    - "Hochschild1945.Cited_semisimple_representations"
    - "Hochschild1945.Cited_simple_inseparable_center"
    - "Hochschild1945.Cited_inseparable_simple_component"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_natural_homomorphism"
decls:
  - "Hochschild1945.separable_iff_first_cohomology_vanishes"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.separable_iff_first_cohomology_vanishes:
        statement_sha256: "ff829ff8fe906a494fe6ed8f1cafc353d75f54fea8c2a0b63a2afbbe399d5ac3"
        type_hash: "00000000870001d9"
        meaning_hash: "7b333975d16a441a"
    session: "root-theorem41-final-independent"
    author_session: "/root/ci_governance"
title: "Separability and first cohomology"
```

## Statement

A necessary and sufficient condition for an algebra $\mathfrak{A}$ to be separable is that $H^1(\mathfrak{A},\mathfrak{P})=\{0\}$ for every two-sided $\mathfrak{A}$-module $\mathfrak{P}$.

## Proof

Now, let $\mathfrak{A}$ be a separable algebra over $\Phi$, and let $\mathfrak{P}$ be any
two-sided $\mathfrak{A}$-module. $\mathfrak{A}$ has an identity element: $e$, say. [uses `Hochschild1945.Cited_separable_identity`] For any element
$u\in\mathfrak{P}$ we may write $u=e\cdot u+(1-e)\cdot u$, where 1 stands for the
identity operator on $\mathfrak{P}$. This gives a direct decomposition of $\mathfrak{P}$ into
the $\mathfrak{A}$-invariant linear subspaces $e\cdot\mathfrak{P}$ and $(1-e)\cdot\mathfrak{P}$.
If $f$ is any $(1,\mathfrak{P})$-cocycle of $\mathfrak{A}$ we have
\[
(1-e)\cdot f\{a\}=(1-e)\cdot f\{ea\}=(1-e)\cdot f\{e\}\cdot a.
\]
If we set $u=(1-e)\cdot f\{e\}$ we have therefore
$f\{a\}=e\cdot f\{a\}-(a\cdot u-u\cdot a)$. It follows that $f$ cobounds
if and only if the $(1,e\cdot\mathfrak{P})$-cocycle $\hat f$, where
$\hat f\{a\}=e\cdot f\{a\}$, cobounds. Thus, in proving that every
1-dimensional cocycle of $\mathfrak{A}$ cobounds, we may confine our attention to those
two-sided $\mathfrak{A}$-modules $\mathfrak{P}$ for which the identity $e$ of $\mathfrak{A}$ is the left
identity operator.

Since $\mathfrak{A}$ is separable there exists a finite algebraic extension $\Gamma$ of
$\Phi$ such that $\mathfrak{A}_\Gamma$ is the direct sum of full matrix algebras over
$\Gamma$; say $\mathfrak{A}_\Gamma=\Gamma_{n_1}+\cdots+\Gamma_{n_m}$. [uses `Hochschild1945.Cited_separable_splitting`] If $f$ is any
$(1,\mathfrak{P})$-cocycle of $\mathfrak{A}$ over $\Phi$ we define a $(1,\mathfrak{P}_\Gamma)$-cocycle
$f^*$ of $\mathfrak{A}_\Gamma$ by setting
$f^*\{\sum_{i=1}^n\gamma_i a_i\}=\sum_{i=1}^n\gamma_i f\{a_i\}$.
Let $e^q_{i,j}$ $(i,j=1,\cdots,n_q)$ denote the matrix units of $\Gamma_{n_q}$.
Then $e^q_{i,j}e^r_{k,p}=\delta_{q,r}\delta_{j,k}e^r_{i,p}$, and
$\sum_{q=1}^m\sum_{i=1}^{n_q}e^q_{i,i}=e$. Consider now the element
$u^*=\sum_{q=1}^m\sum_{i=1}^{n_q}e^q_{i,1}\cdot f^*\{e^q_{1,i}\}$ of
$\mathfrak{P}_\Gamma$: We have
\[
\begin{aligned}
e^r_{h,t}\cdot u^*-u^*\cdot e^r_{h,t}
&=\sum_{q=1}^{m}\sum_{i=1}^{n_q}e^r_{h,t}e^q_{i,1}\cdot f^*\{e^q_{1,i}\}\\
&\quad-\sum_{q=1}^{m}\sum_{i=1}^{n_q}e^q_{i,1}\cdot
 \bigl(f^*\{e^q_{1,i}e^r_{h,t}\}-e^q_{1,i}\cdot f^*\{e^r_{h,t}\}\bigr)\\
&=\sum_{i=1}^{n_r}e^r_{h,t}e^r_{i,1}\cdot f^*\{e^r_{1,i}\}
 -\sum_{i=1}^{n_r}e^r_{i,1}\cdot f^*\{e^r_{1,i}e^r_{h,t}\}
 +e\cdot f^*\{e^r_{h,t}\}\\
&=f^*\{e^r_{h,t}\}.
\end{aligned}
\]
By linearity, it follows that $f^*\{a^*\}=a^*\cdot u^*-u^*\cdot a^*$, for
every $a^*\in\mathfrak{A}_\Gamma$. In particular, $f\{a\}=a\cdot u^*-u^*\cdot a$,
for every $a\in\mathfrak{A}$. The question of whether there exists an element $u\in\mathfrak{P}$
such that $f\{a\}=a\cdot u-u\cdot a$, for every $a\in\mathfrak{A}$ can be reduced
to the question of whether a certain system of linear equations with coefficients
in $\Phi$ possesses a solution in $\Phi$. The last equation means that there
does exist a solution in $\Gamma$. Hence, there must already be a solution in
$\Phi$, and we have proved that every 1-dimensional cocycle of $\mathfrak{A}$ is a coboundary.

Conversely, suppose that $\mathfrak{A}$ is an algebra over $\Phi$ such that
$H^1(\mathfrak{A},\mathfrak{P})=\{0\}$ for every two-sided module $\mathfrak{P}$. It is known that
under these circumstances $\mathfrak{A}$ is semi-simple\textsuperscript{8}. We shall,
however, reproduce the proof here since it will throw some light on the
significance of the 1-dimensional cohomology groups.

As is well known, a necessary and sufficient condition for an algebra to be
semi-simple is that every representation be completely decomposable into
irreducible parts. This in turn is equivalent to the following condition: If
$\mathfrak{P}$ is any left $\mathfrak{A}$-module, $\mathfrak{Q}$ an $\mathfrak{A}$-invariant subspace of $\mathfrak{P}$,
then there exists a (complementary) $\mathfrak{A}$-invariant subspace $\mathfrak{R}$ such that
$\mathfrak{P}$ is the direct sum of $\mathfrak{Q}$ and $\mathfrak{R}$. [uses `Hochschild1945.Cited_semisimple_representations`]

We shall show that this condition is satisfied if all the 1-dimensional
cohomology groups of $\mathfrak{A}$ are $\{0\}$:

Given the left $\mathfrak{A}$-module $\mathfrak{P}$ and an invariant subspace $\mathfrak{Q}$, let us first
choose any linear subspace $\mathfrak{S}$ of $\mathfrak{P}$ such that $\mathfrak{P}$, as a linear
space, is the direct sum of $\mathfrak{Q}$ and $\mathfrak{S}$. For any $s\in\mathfrak{S}$ and $a\in\mathfrak{A}$
we may write $a\cdot s=S_a\{s\}+Q_a\{s\}$, where $S_a\{s\}$ is a uniquely
determined element of $\mathfrak{S}$ and $Q_a\{s\}$ a uniquely determined element of
$\mathfrak{Q}$. Clearly, $S_a$ and $Q_a$ are linear mappings of $\mathfrak{S}$ into $\mathfrak{S}$ and
$\mathfrak{Q}$ respectively. From the relation $a_1\cdot(a_2\cdot s)=a_1a_2\cdot s$
and the fact that the sum $\mathfrak{Q}+\mathfrak{S}$ is direct we obtain the relations
\[
S_{a_1}S_{a_2}=S_{a_1a_2}\quad\hbox{and}\quad
Q_{a_1}S_{a_2}+a_1*Q_{a_2}=Q_{a_1a_2},
\]
where $a*Q$ is defined by $(a*Q)\{s\}=a\cdot Q\{s\}$.

Now, let $\mathfrak{M}$ denote the linear space of all linear mappings of $\mathfrak{S}$ into
$\mathfrak{Q}$. We make $\mathfrak{M}$ a two-sided $\mathfrak{A}$-module by the definitions:
$(a*M)\{s\}=a\cdot M\{s\}$, $M*a=MS_a$, for $M\in\mathfrak{M}$, $a\in\mathfrak{A}$,
$s\in\mathfrak{S}$. It is easy to see from the above relations that the mapping
$a\to Q_a$ is a $(1,\mathfrak{M})$-cocycle of $\mathfrak{A}$. By our hypothesis, there exists
an element $M_0\in\mathfrak{M}$ such that $Q_a=a*M_0-M_0S_a$, i.e.
$Q_a\{s\}=a\cdot M_0\{s\}-M_0\{S_a\{s\}\}$. Now, consider the mapping
$s\to s-M_0\{s\}$ of $\mathfrak{S}$ into $\mathfrak{P}$. This maps $\mathfrak{S}$ onto some
linear subspace $\mathfrak{R}$ of $\mathfrak{P}$. We have
$a\cdot(s-M_0\{s\})=S_a\{s\}+Q_a\{s\}-a\cdot M_0\{s\}
=S_a\{s\}-M_0\{S_a\{s\}\}$, which shows that $\mathfrak{R}$ is $\mathfrak{A}$-invariant.
It is obvious that the mapping $s\to s-M_0\{s\}$ is a linear isomorphism,
whence $\dim(\mathfrak{R})=\dim(\mathfrak{S})$. Furthermore, it is easy to see that
$\mathfrak{R}\cap\mathfrak{Q}=\{0\}$. Hence $\mathfrak{P}$ is the direct sum of $\mathfrak{Q}$ and $\mathfrak{R}$.
This completes the proof that $\mathfrak{A}$ is semi-simple.

Hence, what we have to show now is that if $\mathfrak{A}$ is semi-simple and inseparable
there exist a two-sided $\mathfrak{A}$-module $\mathfrak{P}$ and a non-cobounding
$(1,\mathfrak{P})$-cocycle of $\mathfrak{A}$. Since $\mathfrak{A}$ must have an inseparable simple
component and since any non-cobounding 1-cocycle of a simple component of $\mathfrak{A}$
can be trivially extended to give a non-cobounding 1-cocycle of $\mathfrak{A}$ we may
suppose from now on that $\mathfrak{A}$ is simple. [uses `Hochschild1945.Cited_inseparable_simple_component`] Then—as is well known—the center $\mathfrak{C}$
of $\mathfrak{A}$ is a field which is algebraic and inseparable over $\Phi$. [uses `Hochschild1945.Cited_simple_inseparable_center`] In the case
where $\mathfrak{A}$ itself is an inseparable extension field of $\Phi$, the result in
question follows immediately from the known theory of derivations—i.e.,
$(1,\mathfrak{C})$-cocycles of $\mathfrak{C}$—in fields of characteristic
$p$.\textsuperscript{9} Of the results of this theory we shall require only
the following lemma:

We can now begin the construction of a non-cobounding 1-cocycle of the simple inseparable algebra $\mathfrak{A}$. If $m$ is the dimension of $\mathfrak{A}$ over its center $\mathfrak{C}$ the regular representation of $\mathfrak{A}$ over $\mathfrak{C}$ provides us with an isomorphic mapping $a\to M_a$ of $\mathfrak{A}$ into the matrix algebra $\mathfrak{C}_m$ ($m$-rowed square matrices with elements in $\mathfrak{C}$). It follows that the definitions $a\cdot M=M_aM$, $M\cdot a=MM_a$ make $\mathfrak{C}_m$ (regarded as a linear space over $\Phi$) a two-sided $\mathfrak{A}$-module.

Now let $D$ be a derivation of $\mathfrak{C}$ over $\Phi$ which does not map all of $\mathfrak{C}$ into zero (such a $D$ exists, by Lemma 4.1). [uses `Hochschild1945.Lem_4_1`] If $M=(c_{ij})$ is any element of $\mathfrak{C}_m$ we define $D\{M\}=(D\{c_{ij}\})$ and verify that this is a derivation of $\mathfrak{C}_m$ over $\Phi$. If we now set $f\{a\}=D\{M_a\}$, it is clear that $f$ is a $(1,\mathfrak{C}_m)$-cocycle of $\mathfrak{A}$. If $c\in\mathfrak{C}$, we must obviously have $M_c=cI_m$, where $I_m$ denotes the identity matrix in $\mathfrak{C}_m$. Hence, $f\{c\}=D\{c\}I_m$, which is different from zero for some $c\in\mathfrak{C}$. On the other hand, if $f$ were a coboundary, we should have a matrix $M_0\in\mathfrak{C}_m$ such that $f\{a\}=M_aM_0-M_0M_a$, for every $a\in\mathfrak{A}$. But this would imply that $f\{c\}=0$, for every $c\in\mathfrak{C}$. Hence, $f$ cannot cobound. Thus, we have proved the following theorem:

[Footnote 8] G. Hochschild, loc. cit., Th. 2.3.

[Footnote 9] F. K. Schmidt, ``\textit{Zusatz bei der Korrektur}'',
Crelle's Journal, Vol. 177, pp. 223–237. R. Baer,
``\textit{Algebraische Theorie der differentiierbaren Funktionen-körper I},''
Sitzungsberichte, Heidelberger Akademie, 1927, p.p. 15–32. N. Jacobson,
``\textit{Abstract Derivations and Lie Algebras},'' Trans. Amer. Math. Soc.,
vol. 42 (1937), p.p. 206–224.

[uses `Hochschild1945.Def_cochain`] [uses `Hochschild1945.Def_2_1`]
[uses `Hochschild1945.Def_2_2`] [uses `Hochschild1945.Def_natural_homomorphism`]

## Description

Characterizes separable algebras by vanishing of first cohomology for every two-sided module.

## Formalization notes

The proof precedes the theorem on printed pp. 61–63. The principal statement
retains the actual source first-cohomology quotient, the scalar-extension
separability predicate, and arbitrary coefficient modules P. There is no local
`sorry` in this proof. The explicitly cited classical results remain external
boundaries.

The forward implication follows the printed order. It first obtains the source
identity e and replaces f by e·f with an explicit inner correction. The
normalized map remains in the same coefficient carrier P, with the proved
equation e·g(a)=g(a), instead of introducing a new subtype for e·P. This is
exactly the source image condition and imposes no unit action on all of P. Scalar
extension uses the actual tensor spaces Γ⊗A and Γ⊗P and the bilinear extension of
the source actions. The source's chosen-basis coefficient algebra is transported
to this tensor algebra through the proved coordinate equivalence. After the
classical finite splitting extension, the primitive is the displayed finite sum
of selected row and column matrix units. The ground-field descent applies a
K-linear coefficient functional τ:Γ→K with τ(1)=1 to the primitive. This is an
explicit realization of the source's linear-system descent, and it does not
require P to be finite dimensional.

For the converse, the proof constructs the actual projected actions S_a and Q_a
on a chosen complement and on the invariant subspace. The off-diagonal cocycle
has coefficients Hom(S,Q). Its inner primitive corrects the projection, whose
kernel is proved equal to the source graph s↦s−M₀(s). The resulting invariant
complement gives semisimplicity through the explicitly cited representation
criterion.

The classical inseparable simple-component reduction is recorded separately in
Cited_inseparable_simple_component. The component is an actual two-sided ideal,
and an algebra retraction fixes its inclusion. Inflating a cocycle along that
retraction and restricting a primitive along the inclusion are proved directly;
no cohomological conclusion is built into the cited structure theorem.

For the simple algebra, the actual center-field equivalence supplies the scalar
action. Simplicity proves that the image of the field identity acts as the
identity on A; no unital algebra structure is assumed in the principal statement.
The regular representation is expressed in a finite basis over the center.
Applying the derivation of Lemma 4.1 entrywise gives the printed matrix cocycle.
At a center scalar matrix, every inner cocycle is zero whereas this cocycle is
nonzero for some scalar. Lemma 4.1 is used only for the finite-dimensional center,
within its explicitly reviewed finite-extension scope.

The source excerpts and footnotes are retained. The additional direct imports
of the cochain, cocycle and coboundary definitions provide the formal context for
converting the actual quotient's vanishing to innerness. The AlgebraIdeal API in
Def_natural_homomorphism supplies the already declared source ideals used by the
classical component theorem; this is a formalization dependency, not a claim that
the original proof cited the later natural-map construction.
-/

namespace Hochschild1945.Theorem41Support
open scoped BigOperators
universe u
variable {K P : Type u} {I : Type} [Field K] [Fintype I] [DecidableEq I]
  [AddCommGroup P] [Module K P]

/-- Matrix units give the balancing identity used in the printed primitive. -/
theorem matrix_units_balance (B : Matrix I I K →ₗ[K] Matrix I I K →ₗ[K] P)
    (i₀ : I) (a : Matrix I I K) :
    (∑ i, B (a * Matrix.single i i₀ 1) (Matrix.single i₀ i 1)) =
      ∑ i, B (Matrix.single i i₀ 1) (Matrix.single i₀ i 1 * a) := by
  classical
  induction a using Matrix.induction_on' with
  | h_zero => simp
  | h_add a b ha hb =>
      simp only [add_mul, mul_add, map_add, LinearMap.add_apply, Finset.sum_add_distrib]
      rw [ha, hb]
  | h_std_basis h t c =>
      have leftsum :
          (∑ i, B (Matrix.single h t c * Matrix.single i i₀ 1) (Matrix.single i₀ i 1)) =
            B (Matrix.single h i₀ c) (Matrix.single i₀ t 1) := by
        rw [Finset.sum_eq_single t]
        · simp
        · intro i _ hit
          simp [Matrix.single_mul_single_of_ne c h t i hit.symm 1]
        · simp
      have rightsum :
          (∑ i, B (Matrix.single i i₀ 1) (Matrix.single i₀ i 1 * Matrix.single h t c)) =
            B (Matrix.single h i₀ 1) (Matrix.single i₀ t c) := by
        rw [Finset.sum_eq_single h]
        · simp
        · intro i _ hih
          simp [Matrix.single_mul_single_of_ne (1 : K) i₀ i h hih c]
        · simp
      rw [leftsum, rightsum]
      have hc (i j : I) : Matrix.single i j c = c • Matrix.single i j (1 : K) := by
        simp [Matrix.smul_single]
      rw [hc h i₀, hc i₀ t, map_smul, LinearMap.smul_apply, map_smul]

/-- The source matrix-unit sum is an inner primitive when the left identity acts as one. -/
theorem matrix_inner_of_left_identity
    (M : TwoSidedModule K (Matrix I I K) P) (i₀ : I)
    (f : Matrix I I K →ₗ[K] P)
    (hunit : ∀ a, M.left 1 (f a) = f a)
    (hder : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  classical
  let B : Matrix I I K →ₗ[K] Matrix I I K →ₗ[K] P :=
    LinearMap.compl₂ M.left f
  let p : P := ∑ i, M.left (Matrix.single i i₀ 1) (f (Matrix.single i₀ i 1))
  refine ⟨p, fun a => ?_⟩
  have balance := matrix_units_balance B i₀ a
  change (∑ i, M.left (a * Matrix.single i i₀ 1) (f (Matrix.single i₀ i 1))) =
    ∑ i, M.left (Matrix.single i i₀ 1) (f (Matrix.single i₀ i 1 * a)) at balance
  simp_rw [hder, map_add, ← M.left_assoc] at balance
  simp only [Finset.sum_add_distrib] at balance
  have diagonal :
      (∑ i, M.left (Matrix.single i i₀ 1 * Matrix.single i₀ i 1) (f a)) = f a := by
    simp only [Matrix.single_mul_single_same, one_mul]
    rw [← LinearMap.sum_apply, ← map_sum, Matrix.sum_single_one, hunit]
  rw [diagonal] at balance
  have leftp : M.left a p =
      ∑ i, M.left (a * Matrix.single i i₀ 1) (f (Matrix.single i₀ i 1)) := by
    simp only [p, map_sum, M.left_assoc]
  have rightp : M.right p a =
      ∑ i, M.left (Matrix.single i i₀ 1) (M.right (f (Matrix.single i₀ i 1)) a) := by
    simp only [p, map_sum, LinearMap.sum_apply, M.left_right]
  rw [leftp, rightp, balance]
  abel

/-- Project a derivation onto the left identity image; the discarded summand is
an explicitly inner derivation, as in the first paragraph of the source proof. -/
theorem normalize_derivation {A : Type u} [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (M : TwoSidedModule K A P) (e : A) (he : ∀ a, e * a = a ∧ a * e = a)
    (f : A →ₗ[K] P)
    (hder : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ (g : A →ₗ[K] P) (u : P),
      (∀ a, M.left e (g a) = g a) ∧
      (∀ a b, g (a * b) = M.left a (g b) + M.right (g a) b) ∧
      (∀ a, f a = g a - (M.left a u - M.right u a)) := by
  let g : A →ₗ[K] P := (M.left e).comp f
  let u : P := f e - M.left e (f e)
  have g_apply (a : A) : g a = M.left e (f a) := rfl
  have ee (p : P) : M.left e (M.left e p) = M.left e p := by
    rw [← M.left_assoc, (he e).1]
  have leftright (a : A) : M.left e (M.right (f e) a) = 0 := by
    have h := congrArg (M.left e) (hder e a)
    rw [(he a).1, map_add, ee] at h
    apply add_left_cancel (a := M.left e (f a))
    simpa only [add_zero] using h.symm
  refine ⟨g, u, ?_, ?_, ?_⟩
  · intro a
    exact ee (f a)
  · intro a b
    simp only [g_apply, hder, map_add, ← M.left_assoc, (he a).1, (he a).2,
      M.left_right]
  · intro a
    have huL : M.left a u = 0 := by
      simp only [u, map_sub, ← M.left_assoc, (he a).2, sub_self]
    have huR : M.right u a = M.right (f e) a := by
      simp only [u, map_sub, LinearMap.sub_apply, M.left_right, leftright, sub_zero]
    rw [huL, huR, g_apply, zero_sub, sub_neg_eq_add]
    simpa only [(he a).1] using hder e a

/-- The printed matrix-unit construction works for arbitrary two-sided modules;
no identity action is assumed on the coefficient space. -/
theorem matrix_derivation_inner
    (M : TwoSidedModule K (Matrix I I K) P) (i₀ : I)
    (f : Matrix I I K →ₗ[K] P)
    (hder : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  obtain ⟨g, u, hunit, hg, hfg⟩ := normalize_derivation M 1 (fun a => ⟨one_mul a, mul_one a⟩) f hder
  obtain ⟨v, hv⟩ := matrix_inner_of_left_identity M i₀ g hunit hg
  refine ⟨v - u, fun a => ?_⟩
  rw [hfg, hv, map_sub, map_sub, LinearMap.sub_apply]
  abel

/-- A finite balanced pair family turns the Leibniz identity into the printed
inner primitive; matrix units supply both hypotheses below. -/
theorem balanced_family_inner {A : Type u} {T : Type} [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    [Fintype T] (M : TwoSidedModule K A P) (x y : T → A) (e : A)
    (hdiag : ∑ i, x i * y i = e)
    (hbalance : ∀ (B : A →ₗ[K] A →ₗ[K] P) a,
      (∑ i, B (a * x i) (y i)) = ∑ i, B (x i) (y i * a))
    (f : A →ₗ[K] P) (hunit : ∀ a, M.left e (f a) = f a)
    (hder : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  classical
  let B : A →ₗ[K] A →ₗ[K] P := LinearMap.compl₂ M.left f
  let p : P := ∑ i, M.left (x i) (f (y i))
  refine ⟨p, fun a => ?_⟩
  have balance := hbalance B a
  change (∑ i, M.left (a * x i) (f (y i))) =
    ∑ i, M.left (x i) (f (y i * a)) at balance
  simp_rw [hder, map_add, ← M.left_assoc] at balance
  simp only [Finset.sum_add_distrib] at balance
  have diagonal : (∑ i, M.left (x i * y i) (f a)) = f a := by
    rw [← LinearMap.sum_apply, ← map_sum, hdiag, hunit]
  rw [diagonal] at balance
  have leftp : M.left a p = ∑ i, M.left (a * x i) (f (y i)) := by
    simp only [p, map_sum, M.left_assoc]
  have rightp : M.right p a = ∑ i, M.left (x i) (M.right (f (y i)) a) := by
    simp only [p, map_sum, LinearMap.sum_apply, M.left_right]
  rw [leftp, rightp, balance]
  abel

variable {Q : Type} [Fintype Q] [DecidableEq Q] {J : Q → Type}
  [∀ q, Fintype (J q)] [∀ q, DecidableEq (J q)]

/-- The balancing relation remains valid for a finite product of matrix blocks. -/
theorem matrix_blocks_balance
    (B : (∀ q, Matrix (J q) (J q) K) →ₗ[K] (∀ q, Matrix (J q) (J q) K) →ₗ[K] P)
    (i₀ : ∀ q, J q) (a : ∀ q, Matrix (J q) (J q) K) :
    (∑ q : Q, ∑ i : J q, B (a * Pi.single q (Matrix.single i (i₀ q) 1))
      (Pi.single q (Matrix.single (i₀ q) i 1))) =
    ∑ q : Q, ∑ i : J q, B (Pi.single q (Matrix.single i (i₀ q) 1))
      (Pi.single q (Matrix.single (i₀ q) i 1) * a) := by
  apply Finset.sum_congr rfl
  intro q _
  let emb := LinearMap.single K (fun q => Matrix (J q) (J q) K) q
  have h := matrix_units_balance (LinearMap.compl₂ (B.comp emb) emb) (i₀ q) (a q)
  simpa only [emb, LinearMap.compl₂_apply, LinearMap.comp_apply, LinearMap.single_apply,
    Pi.single_mul_right, Pi.single_mul_left] using h

/-- The products of the selected row/column units add up to the product identity. -/
theorem matrix_blocks_diagonal (i₀ : ∀ q, J q) :
    (∑ q : Q, ∑ i : J q, (Pi.single q (Matrix.single i (i₀ q) 1) : ∀ q, Matrix (J q) (J q) K) *
      Pi.single q (Matrix.single (i₀ q) i 1)) = 1 := by
  simp only [← Pi.single_mul, Matrix.single_mul_single_same, one_mul]
  have hq (q : Q) :
      (∑ i, (Pi.single q (Matrix.single i i (1 : K)) : ∀ q, Matrix (J q) (J q) K)) =
        Pi.single q 1 := by
    change (∑ i, (LinearMap.single K (fun q => Matrix (J q) (J q) K) q)
      (Matrix.single i i 1)) = _
    rw [← map_sum, Matrix.sum_single_one]
    rfl
  simp_rw [hq]
  exact LinearMap.sum_single_apply (fun q => Matrix (J q) (J q) K) 1

/-- Every derivation on a finite product of full matrix algebras has the source
matrix-unit primitive, including modules with nonunital actions. -/
theorem matrix_blocks_derivation_inner
    (M : TwoSidedModule K (∀ q, Matrix (J q) (J q) K) P) (i₀ : ∀ q, J q)
    (f : (∀ q, Matrix (J q) (J q) K) →ₗ[K] P)
    (hder : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  classical
  obtain ⟨g, u, hunit, hg, hfg⟩ := normalize_derivation M 1 (fun a => ⟨one_mul a, mul_one a⟩) f hder
  let x (t : Sigma J) : ∀ q, Matrix (J q) (J q) K := Pi.single t.1 (Matrix.single t.2 (i₀ t.1) 1)
  let y (t : Sigma J) : ∀ q, Matrix (J q) (J q) K := Pi.single t.1 (Matrix.single (i₀ t.1) t.2 1)
  have hdiag : ∑ i, x i * y i = 1 := by
    simpa only [Fintype.sum_sigma, x, y] using matrix_blocks_diagonal (K := K) i₀
  have hbal (B : (∀ q, Matrix (J q) (J q) K) →ₗ[K] (∀ q, Matrix (J q) (J q) K) →ₗ[K] P) a : (∑ i, B (a * x i) (y i)) = ∑ i, B (x i) (y i * a) := by
    simpa only [Fintype.sum_sigma, x, y] using matrix_blocks_balance B i₀ a
  obtain ⟨v, hv⟩ := balanced_family_inner M x y 1 hdiag hbal g hunit hg
  refine ⟨v - u, fun a => ?_⟩
  rw [hfg, hv, map_sub, map_sub, LinearMap.sub_apply]
  abel

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
open scoped TensorProduct
variable {K Γ X Y Z : Type u} [Field K] [Field Γ] [Algebra K Γ]
  [AddCommGroup X] [Module K X] [AddCommGroup Y] [Module K Y]
  [AddCommGroup Z] [Module K Z]

/-- Extend a mixed bilinear map by multiplying the two coefficient factors. -/
noncomputable def extendBilinear (B : X →ₗ[K] Y →ₗ[K] Z) :
    Γ ⊗[K] X →ₗ[Γ] Γ ⊗[K] Y →ₗ[Γ] Γ ⊗[K] Z :=
  ((LinearMap.baseChangeHom K Γ Y Z).comp B).liftBaseChange Γ

/-- Scalar extension of a mixed bilinear map agrees with its coefficient formula. -/
@[simp] theorem extendBilinear_tmul (B : X →ₗ[K] Y →ₗ[K] Z)
    (r s : Γ) (x : X) (y : Y) :
    extendBilinear B (r ⊗ₜ[K] x) (s ⊗ₜ[K] y) = (r * s) ⊗ₜ[K] B x y := by
  simp [extendBilinear, LinearMap.smul_apply, TensorProduct.smul_tmul']

variable {A P : Type u} [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

omit [SMulCommClass K A A] [IsScalarTower K A A] in
/-- A finite ground-field basis extends to a finite basis over the larger field. -/
theorem basechangeFiniteDimensional : FiniteDimensional Γ (Γ ⊗[K] A) :=
  ((Module.finBasis K A).baseChange Γ).finiteDimensional_of_finite

attribute [local instance] basechangeFiniteDimensional

/-- Extend the two source actions to coefficient tensors without restricting P. -/
noncomputable def basechangeModule (M : TwoSidedModule K A P) :
    TwoSidedModule Γ (Γ ⊗[K] A) (Γ ⊗[K] P) where
  left := extendBilinear M.left
  right := extendBilinear M.right
  left_assoc := by
    intro a b p
    induction a using TensorProduct.inductionOn with
    | tmul r a =>
      induction b using TensorProduct.inductionOn with
      | tmul s b =>
        induction p using TensorProduct.inductionOn with
        | tmul t p =>
          simp [Algebra.TensorProduct.tmul_mul_tmul, M.left_assoc, mul_assoc]
        | add p q hp hq => simp only [map_add, hp, hq]
      | add b c hb hc => simp only [mul_add, map_add, LinearMap.add_apply, hb, hc]
    | add a b ha hb => simp only [add_mul, map_add, LinearMap.add_apply, ha, hb]
  right_assoc := by
    intro p a b
    induction p using TensorProduct.inductionOn with
    | tmul r p =>
      induction a using TensorProduct.inductionOn with
      | tmul s a =>
        induction b using TensorProduct.inductionOn with
        | tmul t b =>
          simp [Algebra.TensorProduct.tmul_mul_tmul, M.right_assoc, mul_assoc]
        | add a b ha hb => simp only [mul_add, map_add, ha, hb]
      | add a b ha hb => simp only [add_mul, map_add, LinearMap.add_apply, ha, hb]
    | add p q hp hq => simp only [map_add, LinearMap.add_apply, hp, hq]
  left_right := by
    intro a p b
    induction a using TensorProduct.inductionOn with
    | tmul r a =>
      induction p using TensorProduct.inductionOn with
      | tmul s p =>
        induction b using TensorProduct.inductionOn with
        | tmul t b => simp [M.left_right, mul_assoc]
        | add a b ha hb => simp only [map_add, ha, hb]
      | add p q hp hq => simp only [map_add, LinearMap.add_apply, hp, hq]
    | add a b ha hb => simp only [map_add, LinearMap.add_apply, ha, hb]

/-- A source derivation extends linearly to a derivation over the enlarged field. -/
theorem basechange_derivation (M : TwoSidedModule K A P) (f : A →ₗ[K] P)
    (hf : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b)
    (a b : Γ ⊗[K] A) :
    f.baseChange Γ (a * b) =
      (basechangeModule M).left a (f.baseChange Γ b) +
        (basechangeModule M).right (f.baseChange Γ a) b := by
  induction a using TensorProduct.inductionOn with
  | tmul r a =>
    induction b using TensorProduct.inductionOn with
    | tmul s b =>
      simp [basechangeModule, Algebra.TensorProduct.tmul_mul_tmul, hf, TensorProduct.tmul_add]
    | add b c hb hc => simp [mul_add, map_add, hb, hc, add_add_add_comm]
  | add a b ha hb => simp [add_mul, map_add, LinearMap.add_apply, ha, hb, add_add_add_comm]

/-- Restricting the extended left action to a ground-field algebra element is base change. -/
theorem basechange_left_one (M : TwoSidedModule K A P) (a : A) (v : Γ ⊗[K] P) :
    (basechangeModule M).left ((1 : Γ) ⊗ₜ[K] a) v = (M.left a).baseChange Γ v := by
  induction v using TensorProduct.inductionOn with
  | tmul s p => simp [basechangeModule]
  | add x y hx hy => simp [map_add, hx, hy]

/-- Restricting the extended right action gives the base change of right evaluation. -/
theorem basechange_right_one (M : TwoSidedModule K A P) (a : A) (v : Γ ⊗[K] P) :
    (basechangeModule M).right v ((1 : Γ) ⊗ₜ[K] a) = (M.right.flip a).baseChange Γ v := by
  induction v using TensorProduct.inductionOn with
  | tmul s p => simp [basechangeModule]
  | add x y hx hy => simp [map_add, LinearMap.add_apply, hx, hy]

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
open scoped TensorProduct
variable {K Γ P Q : Type u} [Field K] [Field Γ] [Algebra K Γ]
  [AddCommGroup P] [Module K P] [AddCommGroup Q] [Module K Q]

/-- Apply a K-linear coefficient functional to the scalar-extension factor.
This is the source's descent of a linear system, expressed on formal tensors. -/
def scalarContraction (τ : Γ →ₗ[K] K) : Γ ⊗[K] P →ₗ[K] P :=
  (TensorProduct.lid K P).toLinearMap.comp (TensorProduct.map τ LinearMap.id)

/-- On a pure tensor, coefficient contraction is scalar multiplication by τ. -/
@[simp] theorem scalarContraction_tmul (τ : Γ →ₗ[K] K) (c : Γ) (p : P) :
    scalarContraction τ (c ⊗ₜ[K] p) = τ c • p := by
  simp [scalarContraction]

/-- Coefficient contraction commutes with every ground-field linear map. -/
theorem scalarContraction_baseChange (τ : Γ →ₗ[K] K) (f : P →ₗ[K] Q)
    (x : Γ ⊗[K] P) :
    scalarContraction τ (f.baseChange Γ x) = f (scalarContraction τ x) := by
  induction x using TensorProduct.inductionOn with
  | tmul c p => simp
  | add x y hx hy => simp [hx, hy]

/-- A field extension admits a ground-field linear coefficient retraction
which fixes one. Choosing a dual functional is elementary vector-space algebra. -/
theorem exists_scalar_retraction : ∃ τ : Γ →ₗ[K] K, τ 1 = 1 :=
  Module.Projective.exists_dual_eq_one K (one_ne_zero : (1 : Γ) ≠ 0)

/-- An inner primitive after extending coefficients descends by taking the
coefficient functional with τ(1)=1. The coefficient module can be infinite dimensional. -/
theorem inner_primitive_descends
    {A : Type u} [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (M : TwoSidedModule K A P) (f : A →ₗ[K] P) (v : Γ ⊗[K] P)
    (hv : ∀ a : A, (1 : Γ) ⊗ₜ[K] f a =
      (M.left a).baseChange Γ v -
        (M.right.flip a).baseChange Γ v) :
    ∃ p : P, ∀ a : A, f a = M.left a p - M.right p a := by
  obtain ⟨τ, hτ⟩ := exists_scalar_retraction (K := K) (Γ := Γ)
  refine ⟨scalarContraction τ v, fun a => ?_⟩
  have hh := congrArg (scalarContraction τ) (hv a)
  simpa only [scalarContraction_tmul, hτ, one_smul, map_sub,
    scalarContraction_baseChange, LinearMap.flip_apply] using hh

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
variable {K A B : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
  [IsScalarTower K B B] [FiniteDimensional K B]

/-- The inverse of an actual multiplicative linear equivalence is an algebra
homomorphism, so coefficient actions can be pulled back along it. -/
def inverseNonUnitalHom (e : A ≃ₗ[K] B)
    (he : ∀ a b, e (a*b) = e a * e b) : B →ₙₐ[K] A where
  toFun := e.symm
  map_zero' := e.symm.map_zero
  map_add' := e.symm.map_add
  map_smul' := e.symm.map_smul
  map_mul' := by
    intro b b'
    apply e.injective
    rw [e.apply_symm_apply, he, e.apply_symm_apply, e.apply_symm_apply]

/-- Universal innerness transfers along the source's actual algebra
isomorphism to the split matrix algebra. Both the pulled-back actions and the
cocycle are explicit; the primitive is evaluated back at e(a). -/
theorem inner_derivations_of_multiplicative_equiv (e : A ≃ₗ[K] B)
    (he : ∀ a b, e (a*b) = e a * e b)
    (hinner : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K B V) (f : B →ₗ[K] V),
      (∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) →
      ∃ v : V, ∀ a, f a = M.left a v - M.right v a)
    (V : Type u) [AddCommGroup V] [Module K V]
    (M : TwoSidedModule K A V) (f : A →ₗ[K] V)
    (hf : ∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) :
    ∃ v : V, ∀ a, f a = M.left a v - M.right v a := by
  let π := inverseNonUnitalHom e he
  let N := restrictModule M π
  let g := f.comp e.symm.toLinearMap
  have hg : ∀ a b, g (a*b) = N.left a (g b) + N.right (g a) b := by
    intro a b
    change f (π (a*b)) = M.left (π a) (f (π b)) + M.right (f (π a)) (π b)
    rw [map_mul]
    exact hf (π a) (π b)
  obtain ⟨v, hv⟩ := hinner V N g hg
  refine ⟨v, fun a => ?_⟩
  have hh := hv (e a)
  change f (e.symm (e a)) = M.left (e.symm (e a)) v - M.right v (e.symm (e a)) at hh
  simpa only [e.symm_apply_apply] using hh

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- Restrict a representation to an invariant subspace. -/
def subspaceAction (ρ : A →ₙₐ[K] Module.End K P) (Q : Submodule K P)
    (hQ : ∀ a p, p ∈ Q → ρ a p ∈ Q) : A →ₗ[K] Q →ₗ[K] Q where
  toFun a := (ρ a).restrict (hQ a)
  map_add' := by intros; ext; simp
  map_smul' := by intros; ext; simp

/-- Project the action on a linear complement back into that complement. -/
noncomputable def complementAction (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S) : A →ₗ[K] S →ₗ[K] S where
  toFun a := (S.projectionOnto Q h.symm).comp ((ρ a).comp S.subtype)
  map_add' := by intros; ext; simp
  map_smul' := by intros; ext; simp

/-- The off-diagonal part of the representation relative to Q and S. -/
noncomputable def offDiagonal (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S) : A →ₗ[K] S →ₗ[K] Q where
  toFun a := (Q.projectionOnto S h).comp ((ρ a).comp S.subtype)
  map_add' := by intros; ext; simp
  map_smul' := by intros; ext; simp

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- The original action is the sum of its two projected components. -/
theorem action_decomposition (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S) (a : A) (s : S) :
    (offDiagonal ρ Q S h a s : P) + (complementAction ρ Q S h a s : P) = ρ a s :=
  Submodule.projection_add_projection_eq_self h _

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- The induced action on the complement is associative because Q is invariant. -/
theorem complementAction_mul (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S)
    (hQ : ∀ a p, p ∈ Q → ρ a p ∈ Q) (a b : A) (s : S) :
    complementAction ρ Q S h (a * b) s =
      complementAction ρ Q S h a (complementAction ρ Q S h b s) := by
  change S.projectionOnto Q h.symm (ρ (a * b) s) = _
  rw [map_mul]
  change S.projectionOnto Q h.symm (ρ a (ρ b s)) = _
  rw [← action_decomposition ρ Q S h b s, map_add, map_add]
  rw [Submodule.projectionOnto_apply_of_mem_right h.symm
    (hQ a _ (offDiagonal ρ Q S h b s).property), zero_add]
  rfl

omit [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] in
/-- The off-diagonal component satisfies the source one-cocycle equation. -/
theorem offDiagonal_mul (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S)
    (hQ : ∀ a p, p ∈ Q → ρ a p ∈ Q) (a b : A) (s : S) :
    offDiagonal ρ Q S h (a * b) s =
      subspaceAction ρ Q hQ a (offDiagonal ρ Q S h b s) +
      offDiagonal ρ Q S h a (complementAction ρ Q S h b s) := by
  change Q.projectionOnto S h (ρ (a * b) s) = _
  rw [map_mul]
  change Q.projectionOnto S h (ρ a (ρ b s)) = _
  rw [← action_decomposition ρ Q S h b s, map_add, map_add]
  rw [Submodule.projectionOnto_apply_of_mem_left h
    (hQ a _ (offDiagonal ρ Q S h b s).property)]
  rfl

/-- The source bimodule of linear maps from S to the invariant subspace Q. -/
noncomputable def complementHomModule (ρ : A →ₙₐ[K] Module.End K P)
    (Q S : Submodule K P) (h : IsCompl Q S)
    (hQ : ∀ a p, p ∈ Q → ρ a p ∈ Q) : TwoSidedModule K A (S →ₗ[K] Q) where
  left := {
    toFun a := {
      toFun f := (subspaceAction ρ Q hQ a).comp f
      map_add' := by intros; ext; simp
      map_smul' := by intros; ext; simp }
    map_add' := by intros; ext; simp
    map_smul' := by intros; ext; simp }
  right := {
    toFun f := {
      toFun a := f.comp (complementAction ρ Q S h a)
      map_add' := by intros; ext; simp
      map_smul' := by intros; ext; simp }
    map_add' := by intros; ext; simp
    map_smul' := by intros; ext; simp }
  left_assoc := by
    intro a b f
    ext s
    change ρ (a * b) (f s) = ρ a (ρ b (f s))
    rw [map_mul]
    rfl
  right_assoc := by
    intro f a b
    ext s
    exact congrArg (fun z => (f z : P)) (complementAction_mul ρ Q S h hQ a b s).symm
  left_right := by intros; rfl

/-- The kernel of the corrected projection is exactly the source graph
of s mapped to s minus g(s), not merely an abstract complementary space. -/
theorem corrected_projection_kernel (Q S : Submodule K P) (h : IsCompl Q S)
    (g : S →ₗ[K] Q) :
    LinearMap.ker (Q.projectionOnto S h + g.comp (S.projectionOnto Q h.symm)) =
      LinearMap.range (S.subtype - Q.subtype.comp g) := by
  ext x
  constructor
  · intro hx
    obtain ⟨q, s, rfl, _⟩ := Submodule.existsUnique_add_of_isCompl h x
    have hq : q + g s = 0 := by simpa using hx
    refine ⟨s, ?_⟩
    have hq' : q = -g s := eq_neg_of_add_eq_zero_left hq
    change (s : P) - (g s : P) = (q : P) + (s : P)
    rw [hq']
    simp [sub_eq_add_neg, add_comm]
  · rintro ⟨s, rfl⟩
    change (Q.projectionOnto S h + g.comp (S.projectionOnto Q h.symm))
      ((s : P) - (g s : P)) = 0
    simp

/-- The source off-diagonal cocycle is inner if all derivations with arbitrary
bimodule coefficients are inner; correcting the initial projection then gives
an invariant complement. -/
theorem invariant_complement_of_inner_derivations
    (hinner : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V) (f : A →ₗ[K] V),
      (∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) →
      ∃ v : V, ∀ a, f a = M.left a v - M.right v a)
    (ρ : A →ₙₐ[K] Module.End K P) (Q : Submodule K P)
    (hQ : ∀ a p, p ∈ Q → ρ a p ∈ Q) :
    ∃ R : Submodule K P, IsCompl Q R ∧ ∀ a p, p ∈ R → ρ a p ∈ R := by
  classical
  obtain ⟨S, hS⟩ := Q.exists_isCompl
  let M := complementHomModule ρ Q S hS hQ
  let F := offDiagonal ρ Q S hS
  have hF : ∀ a b, F (a * b) = M.left a (F b) + M.right (F a) b := by
    intro a b
    ext s
    exact congrArg (fun q : Q => (q : P)) (offDiagonal_mul ρ Q S hS hQ a b s)
  obtain ⟨g, hg⟩ := hinner (S →ₗ[K] Q) M F hF
  let t : P →ₗ[K] Q := Q.projectionOnto S hS + g.comp (S.projectionOnto Q hS.symm)
  have ht : ∀ q : Q, t q = q := by intro q; simp [t]
  refine ⟨LinearMap.range (S.subtype - Q.subtype.comp g), ?_, ?_⟩
  · rw [← corrected_projection_kernel Q S hS g]
    exact LinearMap.isCompl_of_proj ht
  rw [← corrected_projection_kernel Q S hS g]
  have hcomm : ∀ a x, t (ρ a x) = subspaceAction ρ Q hQ a (t x) := by
    intro a x
    obtain ⟨q, s, rfl, _⟩ := Submodule.existsUnique_add_of_isCompl hS x
    have hgs := congrArg (fun f : S →ₗ[K] Q => f s) (hg a)
    change F a s = subspaceAction ρ Q hQ a (g s) -
      g (complementAction ρ Q S hS a s) at hgs
    have hq : t (ρ a (q : P)) = subspaceAction ρ Q hQ a q := by
      change t ((subspaceAction ρ Q hQ a q : Q) : P) = _
      exact ht _
    rw [map_add, map_add, hq]
    have hs : t (ρ a (s : P)) = subspaceAction ρ Q hQ a (g s) := by
      change F a s + g (complementAction ρ Q S hS a s) = _
      rw [hgs, sub_add_cancel]
    rw [hs]
    simp [t]
  intro a p hp
  change t p = 0 at hp
  change t (ρ a p) = 0
  rw [hcomm, hp, map_zero]

open scoped TensorProduct

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


/-- Vanishing of the actual source first-cohomology quotient makes every
bimodule derivation inner. No dimension restriction is imposed on V. -/
theorem inner_derivations_of_first_cohomology_vanishes
    (hH : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V), Subsingleton (Cohomology M 1))
    (V : Type u) [AddCommGroup V] [Module K V]
    (M : TwoSidedModule K A V) (f : A →ₗ[K] V)
    (hf : ∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) :
    ∃ v : V, ∀ a, f a = M.left a v - M.right v a := by
  have hf' : IsCocycle M 1 f := (cocycle_one_iff M f).mpr hf
  obtain ⟨v, hv⟩ := (first_cohomology_vanishes_iff M).mp (hH V M) f hf'
  refine ⟨v, fun a => ?_⟩
  have heq := congrArg (fun g : Cochain K A V 1 => g a) hv
  exact heq.trans (delta_zero_apply M v a)

/-- The first converse step of Theorem 4.1 follows the source invariant
complement construction and its explicitly cited classical criterion. -/
theorem semisimple_of_first_cohomology_vanishes
    (hH : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V), Subsingleton (Cohomology M 1)) :
    Semisimple K A := by
  apply (cited_semisimple_representations K A).mpr
  intro V _ _ ρ Q hQ
  exact invariant_complement_of_inner_derivations
    (inner_derivations_of_first_cohomology_vanishes hH) ρ Q hQ

/-- An actual algebra retraction inflates a cocycle and recovers any primitive
by restricting to the embedded component. This is the source's trivial extension
of a simple-component cocycle, with its two-sided actions made explicit. -/
theorem inner_derivations_on_retract
    {B : Type u} [NonUnitalRing B] [Module K B]
    [SMulCommClass K B B] [IsScalarTower K B B] [FiniteDimensional K B]
    (i : B →ₙₐ[K] A) (π : A →ₙₐ[K] B) (hπ : ∀ b : B, π (i b) = b)
    (hinner : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V) (f : A →ₗ[K] V),
      (∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) →
      ∃ v : V, ∀ a, f a = M.left a v - M.right v a)
    (V : Type u) [AddCommGroup V] [Module K V]
    (M : TwoSidedModule K B V) (f : B →ₗ[K] V)
    (hf : ∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) :
    ∃ v : V, ∀ b, f b = M.left b v - M.right v b := by
  let N := restrictModule M π
  let g := f.comp (LinearMap.ofClass π)
  have hg : ∀ a b, g (a*b) = N.left a (g b) + N.right (g a) b := by
    intro a b
    change f (π (a*b)) = M.left (π a) (f (π b)) + M.right (f (π a)) (π b)
    rw [map_mul]
    exact hf (π a) (π b)
  obtain ⟨v, hv⟩ := hinner V N g hg
  refine ⟨v, fun b => ?_⟩
  have hh := hv (i b)
  change f (π (i b)) = M.left (π (i b)) v - M.right v (π (i b)) at hh
  simpa only [hπ] using hh

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
variable {K A C : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [Field C] [Algebra K C]

/-- The two-sided annihilator of a central element is an actual algebra ideal. -/
def centralAnnihilator (z : NonUnitalSubalgebra.center K A) : AlgebraIdeal K A where
  subalgebra := {
    carrier := {a | (z : A) * a = 0}
    zero_mem' := mul_zero _
    add_mem' := by intro x y hx hy; change (z : A) * (x+y) = 0; rw [mul_add, hx, hy, add_zero]
    smul_mem' := by intro c x hx; change (z : A) * (c • x) = 0; rw [mul_smul_comm, hx, smul_zero]
    mul_mem' := by intro x y hx _; change (z : A) * (x*y) = 0; rw [← mul_assoc, hx, zero_mul] }
  mul_mem_left := by
    intro a b hb
    change (z : A) * b = 0 at hb
    change (z : A) * (a*b) = 0
    rw [← mul_assoc, ← (NonUnitalSubalgebra.mem_center_iff.mp z.property a), mul_assoc, hb, mul_zero]
  mul_mem_right := by
    intro a b hb
    change (z : A) * b = 0 at hb
    change (z : A) * (b*a) = 0
    rw [← mul_assoc, hb, zero_mul]

/-- In a simple algebra, the image of one under the multiplicative center-field
isomorphism acts as an identity. This does not assume a unit on the source A. -/
theorem center_one_is_identity
    (hsimple : ∀ I : AlgebraIdeal K A,
      I.subalgebra.toSubmodule = ⊥ ∨ I.subalgebra.toSubmodule = ⊤)
    (e : C ≃ₗ[K] NonUnitalSubalgebra.center K A)
    (hmul : ∀ x y : C, (e (x*y) : A) = (e x : A) * (e y : A)) :
    ∀ a : A, (e 1 : A) * a = a ∧ a * (e 1 : A) = a := by
  have hne : (e 1 : A) ≠ 0 := by
    intro he
    have : e 1 = 0 := Subtype.ext he
    exact one_ne_zero (e.injective (this.trans e.map_zero.symm))
  have hid : (e 1 : A) * (e 1 : A) = e 1 := by rw [← hmul, one_mul]
  have hzero : (centralAnnihilator (e 1)).subalgebra.toSubmodule = ⊥ := by
    rcases hsimple (centralAnnihilator (e 1)) with h | h
    · exact h
    · have hm : (e 1 : A) ∈ (centralAnnihilator (e 1)).subalgebra.toSubmodule := by rw [h]; trivial
      change (e 1 : A) * (e 1 : A) = 0 at hm
      exact (hne (hid.symm.trans hm)).elim
  intro a
  have hm : (e 1 : A) * a - a ∈ (centralAnnihilator (e 1)).subalgebra.toSubmodule := by
    change (e 1 : A) * ((e 1 : A) * a - a) = 0
    rw [mul_sub, ← mul_assoc, hid, sub_self]
  rw [hzero] at hm
  have ha : (e 1 : A) * a = a := sub_eq_zero.mp hm
  exact ⟨ha, (NonUnitalSubalgebra.mem_center_iff.mp (e 1).property a).trans ha⟩

/-- The actual center multiplication gives the regular representation's scalar
module. Its one law is proved from simplicity, rather than assumed. -/
abbrev centerModule (e : C ≃ₗ[K] NonUnitalSubalgebra.center K A)
    (hmul : ∀ x y : C, (e (x*y) : A) = (e x : A) * (e y : A))
    (hone : ∀ a : A, (e 1 : A) * a = a) : Module C A where
  smul c a := (e c : A) * a
  one_smul := hone
  mul_smul := by intro c d a; change (e (c*d) : A) * a = (e c : A) * ((e d : A) * a); rw [hmul, mul_assoc]
  smul_zero := fun c => mul_zero _
  smul_add := fun c a b => mul_add _ _ _
  add_smul := by intro c d a; change (e (c+d) : A) * a = (e c : A) * a + (e d : A) * a; simp [add_mul]
  zero_smul := by intro a; change (e 0 : A) * a = 0; simp

/-- The center-field scalar action agrees with the original ground-field action. -/
abbrev centerScalarTower (e : C ≃ₗ[K] NonUnitalSubalgebra.center K A)
    (hmul : ∀ x y : C, (e (x*y) : A) = (e x : A) * (e y : A))
    (hone : ∀ a : A, (e 1 : A) * a = a) :
    letI := centerModule e hmul hone
    IsScalarTower K C A := by
  let := centerModule e hmul hone
  constructor
  intro k c a
  change (e (k • c) : A) * a = k • ((e c : A) * a)
  rw [map_smul]
  exact smul_mul_assoc k (e c : A) a

/-- Center scalars commute with left multiplication in the source algebra. -/
abbrev centerSmulComm (e : C ≃ₗ[K] NonUnitalSubalgebra.center K A)
    (hmul : ∀ x y : C, (e (x*y) : A) = (e x : A) * (e y : A))
    (hone : ∀ a : A, (e 1 : A) * a = a) :
    letI := centerModule e hmul hone
    SMulCommClass C A A := by
  let := centerModule e hmul hone
  constructor
  intro c a b
  change (e c : A) * (a*b) = a * ((e c : A)*b)
  rw [← mul_assoc, ← NonUnitalSubalgebra.mem_center_iff.mp (e c).property a, mul_assoc]

/-- Center scalars associate with right multiplication in the source algebra. -/
abbrev centerMulTower (e : C ≃ₗ[K] NonUnitalSubalgebra.center K A)
    (hmul : ∀ x y : C, (e (x*y) : A) = (e x : A) * (e y : A))
    (hone : ∀ a : A, (e 1 : A) * a = a) :
    letI := centerModule e hmul hone
    IsScalarTower C A A := by
  let := centerModule e hmul hone
  constructor
  intro c a b
  exact mul_assoc (e c : A) a b

section Regular
variable [Module C A] [IsScalarTower K C A]
  [SMulCommClass C A A] [IsScalarTower C A A]

/-- The regular left representation is linear over the center and over K. -/
def centerRegular : A →ₙₐ[K] Module.End C A where
  toFun a := LinearMap.mul C A a
  map_zero' := by ext; exact zero_mul _
  map_add' := by intros; ext; exact add_mul _ _ _
  map_smul' := by intros; ext; exact smul_mul_assoc _ _ _
  map_mul' := by intros; ext; exact mul_assoc _ _ _

/-- The actual regular representation in a chosen center-field basis. -/
noncomputable def regularMatrix {ι : Type} [Fintype ι] [DecidableEq ι]
    (b : Module.Basis ι C A) : A →ₙₐ[K] Matrix ι ι C where
  toFun a := LinearMap.toMatrix b b (centerRegular (K := K) a)
  map_zero' := by simp
  map_add' := by intros; simp
  map_smul' := by
    intro k a
    rw [map_smul]
    change LinearMap.toMatrix b b (k • centerRegular (K := K) a) = k • _
    exact (LinearMap.toMatrix b b).map_smul_of_tower k _
  map_mul' := by intro a a'; rw [map_mul, LinearMap.toMatrix_mul]

omit [SMulCommClass K A A] in
/-- The regular matrix map is faithful when evaluated at a right identity,
as in the source's isomorphic regular representation. -/
theorem regularMatrix_injective {ι : Type} [Fintype ι] [DecidableEq ι]
    (b : Module.Basis ι C A) (e : A) (he : ∀ a : A, a * e = a) :
    Function.Injective (regularMatrix (K := K) b) := by
  intro a a' haa
  have hh := (LinearMap.toMatrix b b).injective haa
  have hx := congrArg (fun f : A →ₗ[C] A => f e) hh
  change a * e = a' * e at hx
  simpa only [he] using hx

end Regular

section Matrices
variable {ι : Type} [Fintype ι] [DecidableEq ι]

/-- Apply a ground-field linear derivation to every matrix entry, as in the
source regular-representation construction. -/
def matrixDerivative (D : C →ₗ[K] C) : Matrix ι ι C →ₗ[K] Matrix ι ι C where
  toFun X i j := D (X i j)
  map_add' := by intros; ext; exact map_add D _ _
  map_smul' := by intros; ext; exact map_smul D _ _

omit [DecidableEq ι] in
/-- Entrywise differentiation satisfies the matrix Leibniz rule. -/
theorem matrixDerivative_mul (D : C →ₗ[K] C)
    (hD : ∀ x y, D (x*y) = x * D y + D x * y) (X Y : Matrix ι ι C) :
    matrixDerivative D (X*Y) = X * matrixDerivative D Y + matrixDerivative D X * Y := by
  ext i j
  change D (∑ k, X i k * Y k j) =
    (∑ k, X i k * D (Y k j)) + ∑ k, D (X i k) * Y k j
  simp only [map_sum, hD, Finset.sum_add_distrib]

variable [FiniteDimensional K A]

/-- A representation into matrices induces exactly the source two actions. -/
def matrixBimodule (ρ : A →ₙₐ[K] Matrix ι ι C) : TwoSidedModule K A (Matrix ι ι C) where
  left := (LinearMap.mul K (Matrix ι ι C)).comp (LinearMap.ofClass ρ)
  right := {
    toFun X := ((LinearMap.mul K (Matrix ι ι C)) X).comp (LinearMap.ofClass ρ)
    map_add' := by intro X Y; apply LinearMap.ext; intro a; exact add_mul X Y (ρ a)
    map_smul' := by intro k X; apply LinearMap.ext; intro a; exact smul_mul_assoc k X (ρ a) }
  left_assoc := by intro a b X; change ρ (a*b)*X = ρ a*(ρ b*X); rw [map_mul, mul_assoc]
  right_assoc := by intro X a b; change (X*ρ a)*ρ b = X*ρ (a*b); rw [map_mul, mul_assoc]
  left_right := by intro a X b; exact mul_assoc _ _ _

/-- A nonzero center derivation gives an outer cocycle in a matrix
representation that sends center elements to the corresponding scalar matrices. -/
theorem center_matrix_derivation_not_inner [Nonempty ι]
    (ρ : A →ₙₐ[K] Matrix ι ι C) (z : C → A)
    (hz : ∀ c, ρ (z c) = c • (1 : Matrix ι ι C))
    (D : C →ₗ[K] C) (hD : D ≠ 0)
    (hLeibniz : ∀ x y, D (x*y) = x*D y+D x*y) :
    let M := matrixBimodule ρ
    let f := (matrixDerivative D).comp (LinearMap.ofClass ρ)
    (∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) ∧
      ¬ ∃ v, ∀ a, f a = M.left a v - M.right v a := by
  dsimp only
  constructor
  · intro a b
    change matrixDerivative D (ρ (a*b)) = _
    rw [map_mul, matrixDerivative_mul D hLeibniz]
    rfl
  · rintro ⟨v, hv⟩
    apply hD
    ext c
    let i : ι := Classical.choice inferInstance
    have hh := hv (z c)
    change matrixDerivative D (ρ (z c)) = ρ (z c)*v - v*ρ (z c) at hh
    rw [hz, smul_one_mul, mul_smul_one, sub_self] at hh
    have he := congrArg (fun X : Matrix ι ι C => X i i) hh
    change D ((c • (1 : Matrix ι ι C)) i i) = 0 at he
    simpa using he

end Matrices

/-- The source regular matrix construction turns a nonseparable simple center
into a non-inner derivation, contradicting universal innerness. -/
theorem simple_separable_of_inner_derivations [FiniteDimensional K A] [Nontrivial A]
    (hsemi : Semisimple K A)
    (hsimple : ∀ I : AlgebraIdeal K A,
      I.subalgebra.toSubmodule = ⊥ ∨ I.subalgebra.toSubmodule = ⊤)
    (hinner : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V) (f : A →ₗ[K] V),
      (∀ a b, f (a * b) = M.left a (f b) + M.right (f a) b) →
      ∃ v : V, ∀ a, f a = M.left a v - M.right v a) : sourceSeparable K A := by
  classical
  by_contra hins
  obtain ⟨C, cfield, calgebra, hfinite, hCins, e, he⟩ :=
    cited_simple_inseparable_center K A hsemi hsimple hins
  let := cfield
  let := calgebra
  let := hfinite
  have hone := fun a => (center_one_is_identity hsimple e he a).1
  let := centerModule e he hone
  let := centerScalarTower e he hone
  let := centerSmulComm e he hone
  let := centerMulTower e he hone
  let : FiniteDimensional C A := Module.Finite.of_restrictScalars_finite K C A
  let b := Module.finBasis C A
  let ρ := regularMatrix (K := K) b
  let : Nonempty (Fin (Module.finrank C A)) := ⟨⟨0, Module.finrank_pos⟩⟩
  have hz : ∀ c : C, ρ (e c : A) = c • 1 := by
    intro c
    have hreg : centerRegular (K := K) (e c : A) = c • (LinearMap.id : A →ₗ[C] A) := by
      ext a
      rfl
    change LinearMap.toMatrix b b (centerRegular (K := K) (e c : A)) = _
    rw [hreg, map_smul, LinearMap.toMatrix_id]
  have hD : ∃ D : C →ₗ[K] C, D ≠ 0 ∧
      ∀ x y, D (x*y) = x*D y+D x*y := by
    rcases CharP.exists' K with hchar | ⟨p, hp, hchar⟩
    · let := hchar
      exact (hCins inferInstance).elim
    · let := hp
      let := hchar
      exact inseparable_field_derivation K C p hCins
  obtain ⟨D, hne, hLeibniz⟩ := hD
  obtain ⟨hcocycle, houter⟩ := center_matrix_derivation_not_inner ρ (fun c => (e c : A)) hz D hne hLeibniz
  exact houter (hinner _ (matrixBimodule ρ) ((matrixDerivative D).comp (LinearMap.ofClass ρ)) hcocycle)

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
/-- The complete source converse: universal H¹ vanishing first gives invariant
complements, then excludes every inseparable simple factor using the actual
center derivation and regular matrices. -/
theorem separable_of_first_cohomology_vanishes (K A : Type u)
    [Field K] [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (hH : ∀ (V : Type u) [AddCommGroup V] [Module K V]
      (M : TwoSidedModule K A V), Subsingleton (Cohomology M 1)) : sourceSeparable K A := by
  have hinner := inner_derivations_of_first_cohomology_vanishes hH
  have hsemi := semisimple_of_first_cohomology_vanishes hH
  by_contra hins
  obtain ⟨I, hnontrivial, hIsemi, hIsimple, hIins, π, hπ⟩ :=
    cited_inseparable_simple_component K A hsemi hins
  let := hnontrivial
  let : FiniteDimensional K I.subalgebra := idealFiniteDimensional I
  apply hIins
  apply simple_separable_of_inner_derivations hIsemi hIsimple
  exact inner_derivations_on_retract (NonUnitalSubalgebraClass.subtype I.subalgebra) π hπ hinner

end Hochschild1945.Theorem41Support

namespace Hochschild1945.Theorem41Support
universe u
open scoped TensorProduct
attribute [local instance] basechangeFiniteDimensional
  basisExtensionAddCommGroup basisExtensionModule
variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- Use the cited splitting of the actual source basis extension, construct its
matrix-unit primitive, and descend that primitive by coefficient contraction. -/
theorem inner_after_splitting (M : TwoSidedModule K A P)
    (hsep : sourceSeparable K A) (f : A →ₗ[K] P)
    (hf : ∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  classical
  obtain ⟨Γ, fieldΓ, hΓ⟩ := cited_separable_splitting K A hsep
  let := fieldΓ
  obtain ⟨algebraΓ, hΓ⟩ := hΓ
  let := algebraΓ
  obtain ⟨hfinite, m, n, hn, e, he⟩ := hΓ
  let := hfinite
  let tensorEquiv := basisExtensionEquiv (Module.finBasis K A) Γ
  let eT : Γ ⊗[K] A ≃ₗ[Γ] (∀ q : Fin m, Matrix (Fin (n q)) (Fin (n q)) Γ) :=
    tensorEquiv.symm.trans e
  have heT (x y : Γ ⊗[K] A) : eT (x*y) = eT x * eT y := by
    change e (tensorEquiv.symm (x*y)) = e (tensorEquiv.symm x) * e (tensorEquiv.symm y)
    simpa only [basisExtensionMul, tensorEquiv, LinearEquiv.apply_symm_apply] using
      he (tensorEquiv.symm x) (tensorEquiv.symm y)
  have hinner : ∀ (V : Type u) [AddCommGroup V] [Module Γ V]
      (N : TwoSidedModule Γ (∀ q : Fin m, Matrix (Fin (n q)) (Fin (n q)) Γ) V)
      (d : (∀ q : Fin m, Matrix (Fin (n q)) (Fin (n q)) Γ) →ₗ[Γ] V),
      (∀ a b, d (a*b) = N.left a (d b) + N.right (d a) b) →
        ∃ v : V, ∀ a, d a = N.left a v - N.right v a := by
    intro V _ _ N d hd
    exact matrix_blocks_derivation_inner N (fun q => ⟨0, hn q⟩) d hd
  obtain ⟨v, hv⟩ := inner_derivations_of_multiplicative_equiv eT heT hinner
    (Γ ⊗[K] P) (basechangeModule M) (f.baseChange Γ) (basechange_derivation M f hf)
  apply inner_primitive_descends M f v
  intro a
  simpa only [LinearMap.baseChange_tmul, basechange_left_one, basechange_right_one]
    using hv ((1 : Γ) ⊗ₜ[K] a)

/-- The forward source proof first removes the component on which the identity
acts trivially, then splits and descends the normalized derivation. -/
theorem inner_derivations_of_separable (M : TwoSidedModule K A P)
    (hsep : sourceSeparable K A) (f : A →ₗ[K] P)
    (hf : ∀ a b, f (a*b) = M.left a (f b) + M.right (f a) b) :
    ∃ p : P, ∀ a, f a = M.left a p - M.right p a := by
  obtain ⟨e, he⟩ := cited_separable_identity K A hsep
  obtain ⟨g, u, _hfixed, hg, hfg⟩ := normalize_derivation M e he f hf
  obtain ⟨v, hv⟩ := inner_after_splitting M hsep g hg
  refine ⟨v-u, fun a => ?_⟩
  rw [hfg, hv, map_sub, map_sub, LinearMap.sub_apply]
  abel

/-- Every actual source one-cocycle is a coboundary for a separable algebra. -/
theorem first_cohomology_vanishes_of_separable (hsep : sourceSeparable K A)
    (M : TwoSidedModule K A P) : Subsingleton (Cohomology M 1) := by
  apply (first_cohomology_vanishes_iff M).mpr
  intro f hf
  obtain ⟨p, hp⟩ := inner_derivations_of_separable M hsep f ((cocycle_one_iff M f).mp hf)
  refine ⟨p, ?_⟩
  apply LinearMap.ext
  intro a
  exact (hp a).trans (delta_zero_apply M p a).symm

end Hochschild1945.Theorem41Support

namespace Hochschild1945

universe u

/-- **Theorem 4.1** (Hochschild). Separability is equivalent to vanishing of
source first cohomology for every two-sided module, including infinite-dimensional
coefficient spaces. The forward proof uses the source identity correction,
matrix-unit primitive after scalar extension, and coefficient descent. The
converse constructs invariant complements and then an outer regular-matrix
cocycle from an inseparable simple center. The explicitly cited classical
structure results are the only inherited proof boundaries. -/
theorem separable_iff_first_cohomology_vanishes (K A : Type u)
    [Field K] [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] :
    sourceSeparable K A ↔
      ∀ (P : Type u) [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P),
        Subsingleton (Cohomology M 1) := by
  constructor
  · intro h P _ _ M
    exact Theorem41Support.first_cohomology_vanishes_of_separable h M
  · exact Theorem41Support.separable_of_first_cohomology_vanishes K A

end Hochschild1945
