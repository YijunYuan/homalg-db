import HomAlg.Hochschild1945.Def_separable
import Mathlib.Data.Matrix.Basic

/-!
```yaml node
id: "Hochschild1945.Cited_separable_splitting"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 61, 2)"
  pages:
    - 61
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
  proof: []
decls:
  - "Hochschild1945.cited_separable_splitting"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_separable_splitting:
        statement_sha256: "25762f874d65cc72ebdba1d41e78efca667d9f1763829a0e122b96daec4ac1fa"
        type_hash: "00000000667eb7f8"
        meaning_hash: "b03866b671d377cb"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/lean_fixtures"
title: "Finite splitting extension of a separable algebra"
cited:
  source:
    kind: "work"
    ref: "Deuring, Algebren; Van der Waerden, Moderne Algebra; Jacobson, The Theory of Rings (as cited
      in footnote 7)"
    locator: "Hochschild 1945, printed pp. 61; source usage recorded here"
  used_at:
    - 61
  formulation: "verbatim"
```

## Statement

Since $\mathfrak{A}$ is separable there exists a finite algebraic extension $\Gamma$ of
$\Phi$ such that $\mathfrak{A}_\Gamma$ is the direct sum of full matrix algebras over
$\Gamma$; say $\mathfrak{A}_\Gamma=\Gamma_{n_1}+\cdots+\Gamma_{n_m}$.

## Proof

[The document invokes this classical result without supplying its proof. The named cited-result theorem records an unproved external obligation.]

## Description

Records the finite field extension over which a separable algebra becomes a direct sum of full matrix algebras.

## Formalization notes

The source supplies the broad references in footnote 7, without a theorem number. No unverified locator or corrected bibliographic year has been invented.

Source evidence:

[Footnote 7] From here on we shall make use of the classical results in the
theory of separable algebras without giving specific references. The results in
question can be found in any of the standard expositions, such as: Deuring,
``\textit{Algebren}''; Van der Waerden, ``\textit{Moderne Algebra}''; or Jacobson,
loc. cit.
The finite direct sum of matrix blocks is represented by a finite product, with positive matrix sizes and an empty product permitted for the zero algebra. The source basis extension is retained, and the conclusion includes a multiplicative linear equivalence, not just a vector-space equivalence. The field extension is explicitly finite-dimensional over the ground field, hence algebraic.
-/

namespace Hochschild1945

universe u

attribute [local instance] basisExtensionAddCommGroup basisExtensionModule

/-- **Cited result (p. 61, 2)** (Hochschild, classical background). After a
finite field extension, the original basis scalar extension is multiplicatively
linearly equivalent to a finite direct sum of full matrix algebras. A finite
product represents that direct sum, including the empty product for A=0. The
source invokes classical splitting theory without proof; this named external
obligation does not assume the desired decomposition. -/
theorem cited_separable_splitting (K A : Type u) [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (h : sourceSeparable K A) :
    ∃ (Γ : Type u) (field : Field Γ),
      letI := field
      ∃ algebra : Algebra K Γ,
        letI := algebra
        FiniteDimensional K Γ ∧
          ∃ (m : ℕ) (n : Fin m → ℕ), (∀ i, 0 < n i) ∧
            ∃ e : BasisExtension (Module.finrank K A) Γ ≃ₗ[Γ]
                (∀ i : Fin m, Matrix (Fin (n i)) (Fin (n i)) Γ),
              ∀ x y, e (basisExtensionMul (Module.finBasis K A) Γ x y) = e x * e y := by
  sorry

end Hochschild1945
