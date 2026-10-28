import HomAlg.Hochschild1945.Def_separable
import Mathlib.Algebra.Algebra.NonUnitalHom

/-!
```yaml node
id: "Hochschild1945.Cited_semisimple_representations"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 62, 1)"
  pages:
    - 62
  chapter: "4"
tags:
  - "module"
  - "semisimple-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
  proof: []
decls:
  - "Hochschild1945.cited_semisimple_representations"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_semisimple_representations:
        statement_sha256: "3e48b8d08ec2d14cfa9079d35258d542671915360f7a2a9a0e1410856ad4bd57"
        type_hash: "00000000dc67acdb"
        meaning_hash: "17e5a3d620bfc589"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/lean_fixtures"
title: "Semisimplicity and invariant complements"
cited:
  source:
    kind: "folklore"
    locator: "Hochschild 1945, printed pp. 62; source usage recorded here"
  used_at:
    - 62
  formulation: "verbatim"
```

## Statement

As is well known, a necessary and sufficient condition for an algebra to be
semi-simple is that every representation be completely decomposable into
irreducible parts. This in turn is equivalent to the following condition: If
$\mathfrak{P}$ is any left $\mathfrak{A}$-module, $\mathfrak{Q}$ an $\mathfrak{A}$-invariant subspace of $\mathfrak{P}$,
then there exists a (complementary) $\mathfrak{A}$-invariant subspace $\mathfrak{R}$ such that
$\mathfrak{P}$ is the direct sum of $\mathfrak{Q}$ and $\mathfrak{R}$.

## Proof

[The document invokes this classical result without supplying its proof. The named cited-result theorem records an unproved external obligation.]

## Description

Records the classical characterization of semisimplicity by complete reducibility and invariant complements.

## Formalization notes

The source calls this fact well known. It is separate from the following source proof that vanishing first cohomology provides the complement.
A left action is an actual nonunital algebra representation on Module.End. The criterion is the invariant-complement condition printed in the source, for arbitrary coefficient spaces P. No finite-dimensionality or unital-action condition is imposed on P.
-/

namespace Hochschild1945

universe u

/-- **Cited result (p. 62, 1)** (Hochschild, classical background). Every
invariant subspace of every left representation has an invariant complement
exactly when the finite source algebra is semisimple. A nonunital algebra map
to Module.End encodes the source left action without imposing a unit law on P.
The source invokes this classical criterion without proof. -/
theorem cited_semisimple_representations (K A : Type u) [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] :
    Semisimple K A ↔
      ∀ (P : Type u) [AddCommGroup P] [Module K P]
        (ρ : A →ₙₐ[K] Module.End K P) (Q : Submodule K P),
        (∀ a p, p ∈ Q → ρ a p ∈ Q) →
        ∃ R : Submodule K P, IsCompl Q R ∧ ∀ a p, p ∈ R → ρ a p ∈ R := by
  sorry

end Hochschild1945
