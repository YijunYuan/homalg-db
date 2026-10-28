import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism

/-!
```yaml node
id: "Hochschild1945.Cited_inseparable_simple_component"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 62, simple component)"
  pages:
    - 62
  chapter: "4"
tags:
  - "semisimple-algebra"
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Def_natural_homomorphism"
  proof: []
decls:
  - "Hochschild1945.cited_inseparable_simple_component"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_inseparable_simple_component:
        statement_sha256: "04830f2e8bf44aa0cda014d6c9259d02f94a0b74e781443fe0373571d502aaf0"
        type_hash: "000000007679b5fe"
        meaning_hash: "17bad519e4420340"
    session: "ci-simple-component-independent"
    author_session: "/root"
title: "Inseparable simple component of a semisimple algebra"
cited:
  source:
    kind: "folklore"
    locator: "Hochschild 1945, printed p. 62, reduction to a simple inseparable component"
  used_at:
    - 62
  formulation: "editorial"
```

## Statement

[Editorial] A finite-dimensional semisimple but inseparable algebra has a nonzero simple inseparable two-sided ideal which is a direct algebra factor. In particular, there is an algebra projection onto that ideal whose restriction to the ideal is the identity.

## Proof

[The source invokes the classical decomposition into simple components and its separability consequence without proving them. This named cited theorem records that external obligation.]

## Description

Isolates the classical simple-component reduction used before constructing a non-inner derivation on a simple inseparable algebra.

## Formalization notes

Printed p. 62 (PDF p. 6) states: "Since $\mathfrak{A}$ must have an inseparable simple component" before reducing to the simple case. This editorial formulation makes that invoked structural boundary explicit.

The factor is an actual AlgebraIdeal I of A. Nontriviality, semisimplicity, two-sided simplicity and source inseparability are stated explicitly. The algebra projection fixes I. Because I is a two-sided ideal, its intersection with the projection kernel is zero and their products in both orders are zero; the projection also gives their vector-space sum as A. Thus this is a genuine direct algebra factor. No existence of a derivation, failure of innerness or cohomology assertion is assumed.

The source's subsequent inflation of a non-inner derivation is a separate formal proof step. The article-defined sourceSeparable and actual source ideals are retained. This citation remains a named unproved external result and is not part of the foundation boundary.
-/

namespace Hochschild1945
universe u
attribute [local instance] idealFiniteDimensional

/-- **Cited result (p. 62, simple component)** (Hochschild, classical background).
A finite
semisimple inseparable algebra has a nonzero simple inseparable direct factor.
The actual two-sided ideal and algebra projection identify that factor, rather
than postulating any cohomological conclusion. The source invokes this result
without proof; this named external obligation remains explicit. -/
theorem cited_inseparable_simple_component (K A : Type u) [Field K]
    [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
    [FiniteDimensional K A] (hsemi : Semisimple K A) (hins : ¬ sourceSeparable K A) :
    ∃ I : AlgebraIdeal K A,
      Nontrivial I.subalgebra ∧ Semisimple K I.subalgebra ∧
      (∀ J : AlgebraIdeal K I.subalgebra,
        J.subalgebra.toSubmodule = ⊥ ∨ J.subalgebra.toSubmodule = ⊤) ∧
      ¬ sourceSeparable K I.subalgebra ∧
      ∃ π : A →ₙₐ[K] I.subalgebra, ∀ x : I.subalgebra, π x = x := by
  sorry
end Hochschild1945
