# Section 4 foundation proposals

Author-session: /root/lean_fixtures
Date: 2026-10-28
Status: proposed, awaiting an independent review

| Notion | Pinned Mathlib declarations | Source anchor | Permitted scope |
| --- | --- | --- | --- |
| Finite matrices and full matrix algebras | `Matrix`, `Matrix.mul_apply` | Printed p. 61 (PDF p. 5), the full matrix blocks and matrix-unit calculation in section 4 | Coordinate arrays, usual finite-sum multiplication, entrywise linear structure, finite products |
| Algebraic and separable field extensions | `Algebra.IsAlgebraic`, `Algebra.IsSeparable` | Printed p. 62 (PDF p. 6), Lemma 4.1 and the simple-center argument | Classical field-extension/minimal-polynomial terminology only |

The matrix proposal does not import a splitting theorem, a semisimplicity theorem, or any cohomology criterion. Those source-invoked results remain distinct named cited-result proof obligations.

The field proposal does not replace the source definition of separability for an associative algebra. `Hochschild1945.sourceSeparable` still quantifies the original basis scalar extensions and uses their original multiplication. The field predicates appear in the inseparable-field lemma and in the classical center-field citation, where the paper uses them as prior field theory.

Both proposals retain the source's arbitrary ground field. No perfection, characteristic-zero, algebraic-closure, or unital-action assumption is introduced.
