import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism
/-!
```yaml node
id: "Hochschild1945.Cited_semisimple_ideal_structure"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 64, 2)"
  pages:
    - 64
    - 65
  chapter: "6"
tags:
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
  - "Hochschild1945.cited_semisimple_ideal_structure"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_semisimple_ideal_structure:
        statement_sha256: "ee304599018078b90c71b62180b4415d792ddb105381ad1d1e6292df66c0afbc"
        type_hash: "000000004db730fa"
        meaning_hash: "3222dfc3849e7a8d"
    session: "ci-classical-section6-independent"
    author_session: "schema-taxonomy-ideal-2026-10-28"
title: "Ideals in semisimple algebras"
cited:
  source:
    kind: "folklore"
    locator: "Hochschild 1945, printed pp. 64, 65; source usage recorded here"
  used_at:
    - 64
    - 65
  formulation: "editorial"
```

## Statement

[Editorial] An ideal of a finite-dimensional semisimple algebra is semisimple and has an ideal complement in that algebra.

## Proof

[The document invokes this classical result without supplying its proof. It remains an explicit cited boundary with `sorry`, rather than an axiom or hidden assumption.]

## Description

Records the semisimple ideal and complement facts used inside the proof for a general algebra.

## Formalization notes

The general-algebra conclusion remains the locally proved Lem_semisimple_ideal_summand. This cited boundary concerns only ideals inside a semisimple algebra.

Source evidence:

Now, if $\mathfrak{C}$ is any algebra and $\mathfrak{S}$ a semi-simple ideal of $\mathfrak{C}$ then $\mathfrak{C}$ is the direct sum of $\mathfrak{S}$ and another ideal $\mathfrak{T}$. For, if $\mathfrak{H}$ is the radical of $\mathfrak{C}$ we have $\mathfrak{S}\cap\mathfrak{H}=\{0\}$; $\mathfrak{C}/\mathfrak{H}$ is semi-simple and contains the semi-simple ideal $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}\cong\mathfrak{S}$. Hence $\mathfrak{C}/\mathfrak{H}$ is the direct sum of $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}$ and another ideal $\mathfrak{U}$.
-/

namespace Hochschild1945

universe u

variable (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]

attribute [local instance] idealFiniteDimensional

/-- **Cited result (p. 64, 2)**. An ideal in a finite-dimensional semisimple
algebra is semisimple and has a two-sided ideal complement. The ambient
semisimplicity hypothesis distinguishes this classical boundary from the
general-algebra lemma proved from it. -/
theorem cited_semisimple_ideal_structure (hA : Semisimple K A)
    (I : AlgebraIdeal K A) : Semisimple K I.subalgebra ∧
      ∃ J : AlgebraIdeal K A, IsCompl I.subalgebra.toSubmodule J.subalgebra.toSubmodule := by
  sorry

end Hochschild1945
