import HomAlg.Hochschild1945.Def_separable

/-!
```yaml node
id: "Hochschild1945.Cited_separable_identity"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Cited result (p. 61, 1)"
  pages:
    - 61
  chapter: "4"
tags:
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
  proof: []
decls:
  - "Hochschild1945.cited_separable_identity"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cited_separable_identity:
        statement_sha256: "f27b150020e3788e71618d54d492d35930d5bb885e655440b839b3fc4dc63e39"
        type_hash: "00000000efafcbba"
        meaning_hash: "c3905c26c3620c81"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/lean_fixtures"
title: "Identity in a separable algebra"
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

Now, let $\mathfrak{A}$ be a separable algebra over $\Phi$, and let $\mathfrak{P}$ be any
two-sided $\mathfrak{A}$-module. $\mathfrak{A}$ has an identity element: $e$, say.

## Proof

[The document invokes this classical result without supplying its proof. The named cited-result theorem records an unproved external obligation.]

## Description

Records the classical identity-element fact invoked after assuming separability.

## Formalization notes

The source does not assume an identity in its initial algebra definition. This citation is the first place the proof obtains one.

Source evidence:

[Footnote 7] From here on we shall make use of the classical results in the
theory of separable algebras without giving specific references. The results in
question can be found in any of the standard expositions, such as: Deuring,
``\textit{Algebren}''; Van der Waerden, ``\textit{Moderne Algebra}''; or Jacobson,
loc. cit.
The conclusion supplies a two-sided identity as an actual element. No identity is assumed in the algebra structure; the zero algebra is retained.
-/

namespace Hochschild1945

universe u

/-- **Cited result (p. 61, 1)** (Hochschild, classical background). A separable
finite-dimensional algebra has a two-sided identity, including the zero algebra.
The source invokes the classical structure theory cited in footnote 7 without
proof. This is a named external proof obligation, not an added unital hypothesis. -/
theorem cited_separable_identity (K A : Type u) [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (h : sourceSeparable K A) : ∃ e : A, ∀ a : A, e * a = a ∧ a * e = a := by
  sorry

end Hochschild1945
