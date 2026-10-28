import HomAlg.Hochschild1945.Def_two_sided_module
import Mathlib.Algebra.Category.ModuleCat.Basic

/-!
```yaml node
id: "Hochschild1945.Def_cochain"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 59, 2)"
  pages:
    - 59
  chapter: "1"
tags:
  - "cohomology"
  - "module"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_two_sided_module"
  proof: []
decls:
  - "Hochschild1945.cochainSpace"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cochainSpace:
        statement_sha256: "08c4694b4cd03eb4f30a8be3cb485e6d5bf1bdcf75d8ee28b4ef5ab681b6bba4"
        type_hash: "00000000c6f53c17"
        meaning_hash: "afa6b7aeddcabb44"
    session: "ci-firstchapter-independent"
    author_session: "/root/lean_fixtures"
title: "Cochains"
mathlib:
  relation: "variant"
  decls:
    - "MultilinearMap"
  bridge: "Hochschild1945.Bridge_Def_cochain_mathlib"
  note: "The source keeps actual tensor-linear-map cochains; the bridge constructs the multilinear-map
    equivalence and proves its evaluation formula."
```

## Statement

We denote the Kronecker product of $m$ linear spaces isomorphic with the linear
space underlying $\mathfrak{A}$ by $\mathfrak{A}^{(m)}$. If $a_1$, $a_2$, $\cdots$, $a_n$ is a
basis of $\mathfrak{A}$ over $\Phi$, $\mathfrak{A}^{(m)}$ is the $n^m$-dimensional linear space
which is spanned by the elements $a_{i_1}\times a_{i_2}\times\cdots\times a_{i_m}$.
By an $m$-dimensional $\mathfrak{P}$-cochain of $\mathfrak{A}$, briefly an $(m,\mathfrak{P})$-cochain
of $\mathfrak{A}$, is meant a linear mapping of $\mathfrak{A}^{(m)}$ into the two-sided $\mathfrak{A}$-module
$\mathfrak{P}$. By a $(0,\mathfrak{P})$-cochain of $\mathfrak{A}$ we mean simply an element of
$\mathfrak{P}$. The linear space over $\Phi$ formed by all the $(m,\mathfrak{P})$-cochains of
$\mathfrak{A}$ will be denoted by $(\mathfrak{A}^{(m)}:\mathfrak{P})$.

## Description

The source construction is retained with an associative algebra without a required identity. Tensor products and linear maps supply basic linear algebra only; no existing cohomology construction is substituted.

## Formalization notes

The principal `cochainSpace` definition takes the source two-sided module over its finite-dimensional associative, not necessarily unital algebra. `KroneckerPower`, `linearCochainSpace`, and `Cochain` are general linear-algebra carrier helpers. The carrier is independent of the values of the two actions; these are used by the source coboundary.
-/


namespace Hochschild1945

open scoped TensorProduct

universe u

section LinearCarriers

variable (K A P : Type u) [Field K] [AddCommGroup A] [Module K A]
  [AddCommGroup P] [Module K P]

/-- The Kronecker product of `n + 1` copies of the underlying vector space of `A`.
The positive-degree indexing avoids imposing a tensor representative on degree-zero cochains. -/
@[reducible] def KroneckerPower : Nat → ModuleCat.{u} K
  | 0 => ModuleCat.of K A
  | n + 1 => ModuleCat.of K ((KroneckerPower n) ⊗[K] A)

/-- **Definition (unnumbered, p. 59, 2)**. In positive degree these are literally
linear maps out of the source's Kronecker power; in degree zero they are elements of `P`. -/
@[reducible] def linearCochainSpace : Nat → ModuleCat.{u} K
  | 0 => ModuleCat.of K P
  | n + 1 => ModuleCat.of K (KroneckerPower K A n →ₗ[K] P)

/-- The carrier of the vector space of source cochains. -/
abbrev Cochain (n : Nat) : Type u := linearCochainSpace K A P n

end LinearCarriers

/-- **Definition (unnumbered, p. 59, 2)** with the source's algebra and coefficient
module hypotheses attached. Its carrier is the tensor-linear-map space above: the
individual action values are irrelevant to the carrier and enter the later coboundary. -/
def cochainSpace {K A P : Type u} [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
    [FiniteDimensional K A] [AddCommGroup P] [Module K P]
    (_M : TwoSidedModule K A P) (n : Nat) : ModuleCat.{u} K :=
  linearCochainSpace K A P n

end Hochschild1945
