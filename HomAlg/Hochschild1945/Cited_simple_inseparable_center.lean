import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism
import Mathlib.FieldTheory.Separable

/-!
```yaml node
id: "Hochschild1945.Cited_simple_inseparable_center"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 62, 2)"
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
  - "Hochschild1945.cited_simple_inseparable_center"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_simple_inseparable_center:
        statement_sha256: "478f21feb29b63e8ca2713217c0528fe32399c5c74a6c7eb7c00bcb3ded564f3"
        type_hash: "0000000062432170"
        meaning_hash: "95ec81fba77e63f7"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/lean_fixtures"
title: "Center of a simple inseparable algebra"
cited:
  source:
    kind: "folklore"
    locator: "Hochschild 1945, printed pp. 62; source usage recorded here"
  used_at:
    - 62
  formulation: "editorial"
```

## Statement

[Editorial] For a finite-dimensional simple inseparable associative algebra $\mathfrak{A}$ over $\Phi$, its center $\mathfrak{C}$ is a field algebraic and inseparable over $\Phi$.

## Proof

[The document invokes this classical result without supplying its proof. The named cited-result theorem records an unproved external obligation.]

## Description

Makes explicit the classical center-field fact used after reduction to a simple inseparable algebra.

## Formalization notes

The formulation supplies the hypotheses from the preceding source reduction; the precise source context is quoted below. It does not import the later construction of the non-cobounding cocycle.

Source evidence:

Since $\mathfrak{A}$ must have an inseparable simple
component and since any non-cobounding 1-cocycle of a simple component of $\mathfrak{A}$
can be trivially extended to give a non-cobounding 1-cocycle of $\mathfrak{A}$ we may
suppose from now on that $\mathfrak{A}$ is simple. Then—as is well known—the center $\mathfrak{C}$
of $\mathfrak{A}$ is a field which is algebraic and inseparable over $\Phi$.
The source reduction already assumes a semisimple algebra and then selects a nonzero simple component; those hypotheses are explicit. Simplicity means that the scalar-closed two-sided ideals are zero or the whole algebra. The actual commuting subalgebra is multiplicatively linearly equivalent to a finite inseparable field extension. This expresses the center-field conclusion without assuming a field or identity structure on A.
-/

namespace Hochschild1945

universe u

/-- **Cited result (p. 62, 2)** (Hochschild, classical background). In the
source's reduction to a nonzero simple component of a semisimple inseparable
algebra, the actual center is a finite inseparable field extension of K. The
center is represented by its actual commuting subalgebra, with a multiplicative
linear equivalence to a field witness; no field structure is assumed on A.
The source invokes this classical center theorem without proof. -/
theorem cited_simple_inseparable_center (K A : Type u) [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    [Nontrivial A] (hsemi : Semisimple K A)
    (hsimple : ∀ I : AlgebraIdeal K A,
      I.subalgebra.toSubmodule = ⊥ ∨ I.subalgebra.toSubmodule = ⊤)
    (hins : ¬ sourceSeparable K A) :
    ∃ (C : Type u) (field : Field C),
      letI := field
      ∃ algebra : Algebra K C,
        letI := algebra
        FiniteDimensional K C ∧ ¬ Algebra.IsSeparable K C ∧
          ∃ e : C ≃ₗ[K] NonUnitalSubalgebra.center K A,
            ∀ x y : C, (e (x * y) : A) = (e x : A) * (e y : A) := by
  sorry

end Hochschild1945
