import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism
import Mathlib.Algebra.BigOperators.Group.List.Basic
/-!
```yaml node
id: "Hochschild1945.Cited_radical_structure"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 64, 1)"
  pages:
    - 64
  chapter: "6"
tags:
  - "radical"
  - "semisimple-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Def_natural_homomorphism"
  proof: []
decls:
  - "Hochschild1945.cited_radical_quotient"
  - "Hochschild1945.cited_radical_nilpotent"
  - "Hochschild1945.cited_semisimple_inter_radical"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_radical_quotient:
        statement_sha256: "246f27a5824ab64bec0d35e6db154b6cb9707594b04910f273cea230ae1b612f"
        type_hash: "000000008b913a2e"
        meaning_hash: "5904f3d009f06923"
      Hochschild1945.cited_radical_nilpotent:
        statement_sha256: "4b99cbe2a89296142675144176a0b7ef41d587e19ccb21aa4cc73b9973fe63d6"
        type_hash: "00000000c5d9dfa6"
        meaning_hash: "00000000c5d9dfa6"
      Hochschild1945.cited_semisimple_inter_radical:
        statement_sha256: "cef85dcd676208638307f1b842c0c11ff6284be2aca177f46dfa1e097acc28d3"
        type_hash: "00000000fb0e0129"
        meaning_hash: "12a261e63ba9f6ca"
    session: "ci-classical-section6-independent"
    author_session: "schema-taxonomy-ideal-2026-10-28"
title: "Finite-dimensional radical and semisimple quotient"
cited:
  source:
    kind: "folklore"
    locator: "Hochschild 1945, printed pp. 64; source usage recorded here"
  used_at:
    - 64
  formulation: "editorial"
```

## Statement

[Editorial] For the finite-dimensional associative algebra $\mathfrak{B}$ in the extension argument, its radical $\mathfrak{R}$ is nilpotent, and the quotient $\mathfrak{B}/\mathfrak{R}$ is semisimple. A semisimple ideal of $\mathfrak{B}$ has zero intersection with $\mathfrak{R}$, as used in the following paragraph. The zero quotient is permitted by the formal semisimplicity predicate.

## Proof

[The document invokes these classical results without supplying their proofs. They remain explicit cited boundaries, with `sorry`, rather than axioms or hidden assumptions.]

## Description

Isolates the classical radical facts used to reduce the kernel of an extension to a nilpotent ideal.

## Formalization notes

This boundary records nilpotence of the radical, semisimplicity of its quotient, and the zero intersection of a semisimple ideal with the ambient radical, explicitly used in the next paragraph on p. 64. The subsequent homomorphism and kernel calculations are proved in Proposition 6.1 and are not imported conclusions.

Source evidence:

Let $\{\mathfrak{B},\sigma\}$ be any extension of $\mathfrak{A}$, let $\mathfrak{K}$ denote the kernel of the homomorphism $\sigma$, and let $\mathfrak{R}$ denote the radical of $\mathfrak{B}$. Consider $\mathfrak{B}/\mathfrak{R}$: clearly, $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$ is an ideal of $\mathfrak{B}/\mathfrak{R}$ (for $\mathfrak{K}$ is an ideal of $\mathfrak{B}$). Since $\mathfrak{B}/\mathfrak{R}$ is semi-simple (we need not consider the case where $\mathfrak{B}$, and hence also $\mathfrak{K}$, is nilpotent), so is $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$. Further, $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$ is isomorphic with $\mathfrak{K}/\mathfrak{N}$, where $\mathfrak{N}=\mathfrak{K}\cap\mathfrak{R}$. Obviously, $\mathfrak{N}$ is a nilpotent ideal of $\mathfrak{B}$, $\mathfrak{K}/\mathfrak{N}$ is a semi-simple ideal of $\mathfrak{B}/\mathfrak{N}$, and we have the isomorphisms $\mathfrak{A}\cong\mathfrak{B}/\mathfrak{K}\cong(\mathfrak{B}/\mathfrak{N})/(\mathfrak{K}/\mathfrak{N})$.
-/

namespace Hochschild1945

universe u

variable (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]

/-- A quotient by the actual nonunital Jacobson radical. The map is surjective
and its kernel is specified, so the carrier is genuinely a quotient of `A`.
All bundled instances are installed locally by consumers. -/
structure RadicalQuotient where
  carrier : Type u
  [ring : NonUnitalRing carrier]
  [module : Module K carrier]
  [comm : SMulCommClass K carrier carrier]
  [tower : IsScalarTower K carrier carrier]
  [finite : FiniteDimensional K carrier]
  quotient : A →ₙₐ[K] carrier
  surjective : Function.Surjective quotient
  kernel : ∀ a : A, quotient a = 0 ↔
    Unitization.inr a ∈ Ring.jacobson (Unitization K A)
  semisimple : Semisimple K carrier

/-- **Cited result (p. 64, 1)**. The quotient by the Jacobson radical of a
finite-dimensional associative algebra is semisimple. No identity in `A` is
assumed. This is a classical external boundary invoked on source p. 64. -/
theorem cited_radical_quotient : Nonempty (RadicalQuotient K A) := by
  sorry

/-- **Cited result (p. 64, 1) (nilpotence)**. Some positive length annihilates
every product of radical elements. Products are taken in the unitization using
its actual multiplication; the inr inclusion preserves nonempty products. -/
theorem cited_radical_nilpotent :
    ∃ n : ℕ, 0 < n ∧ ∀ a : Fin n → A,
      (∀ i, Unitization.inr (a i) ∈ Ring.jacobson (Unitization K A)) →
      (List.ofFn (fun i => (Unitization.inr (a i) : Unitization K A))).prod = 0 := by
  sorry

attribute [local instance] idealFiniteDimensional

/-- **Cited result (p. 64, 1) (intersection)**. A semisimple ideal meets the
ambient Jacobson radical only in zero, as invoked in the source's next
paragraph. This statement does not assert an ideal complement. -/
theorem cited_semisimple_inter_radical (I : AlgebraIdeal K A)
    (hI : Semisimple K I.subalgebra) (a : A) (ha : a ∈ I.subalgebra)
    (hr : Unitization.inr a ∈ Ring.jacobson (Unitization K A)) : a = 0 := by
  sorry

end Hochschild1945
