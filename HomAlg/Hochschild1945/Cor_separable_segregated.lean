import HomAlg.Hochschild1945.Prop_6_1
import HomAlg.Hochschild1945.Prop_1_1
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Thm_3_1
import HomAlg.Hochschild1945.Thm_4_1
import HomAlg.Hochschild1945.Thm_6_1

/-!
```yaml node
id: "Hochschild1945.Cor_separable_segregated"
doc: "Hochschild1945"
kind: "corollary"
source:
  label: "Corollary (p. 67)"
  pages:
    - 67
  chapter: "6"
tags:
  - "segregated-extension"
  - "separable-algebra"
  - "wedderburn-principal-theorem"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_extension"
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Prop_6_1"
  proof:
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Prop_1_1"
    - "Hochschild1945.Thm_3_1"
    - "Hochschild1945.Thm_4_1"
    - "Hochschild1945.Thm_6_1"
decls:
  - "Hochschild1945.separable_segregated_in_every_extension"
fidelity:
  status: "deviates"
  deviations:
    - kind: "generality"
      what: "Universal segregation quantifies finite-dimensional extension algebras explicitly; coefficient
        modules remain arbitrary."
      why: "The classical radical argument uses finite dimension, and unrestricted extensions give counterexamples
        such as K[x] onto K×K. The theorem's arbitrary-coefficient implication is retained using an explicit
        finite-support reduction."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.separable_segregated_in_every_extension:
        statement_sha256: "5ee32624a8215239a9c6ad9b96f02c8de166f7688634df3d4bf036b58ff920a0"
        type_hash: "0000000043b9b9e7"
        meaning_hash: "98795143191a0f22"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Separable algebras are segregated"
```

## Statement

A separable algebra is segregated in every extension.

## Proof

This, with Theorems 4.1 and 3.1 implies a result which is essentially the classical generalization (to arbitrary ground fields) of Wedderburn's third structure theorem: [uses `Hochschild1945.Thm_6_1`] [uses `Hochschild1945.Thm_4_1`] [uses `Hochschild1945.Thm_3_1`]

[uses `Hochschild1945.Def_2_3`] [uses `Hochschild1945.Def_cochain`] [uses `Hochschild1945.Def_two_sided_module`] [uses `Hochschild1945.Prop_1_1`]

## Description

Deduces segregation of a separable algebra in every extension from the cohomological characterizations.
## Formalization notes

The universal extension assertion is interpreted for finite-dimensional extension
algebras; the general extension definition itself has no dimension restriction.
This scope is necessary: evaluation at 0 and 1 maps K[x] onto the separable
algebra K×K, but no algebra section can produce a nontrivial idempotent in K[x].
Coefficient modules are still arbitrary. Theorem 6.1's forward direction uses
the additional finite-support reduction proved in its technical auxiliary.
The explicit clarification is recorded as a deviation for independent review.


Def_extension is retained as the source statement's extension/segregation
vocabulary. The compiled principal type names SegregatedInEveryExtension from
Prop_6_1, so its direct statement trace records Prop_6_1 rather than unfolding
that predicate into Def_extension. This explains the retained
`deps_diff.declared_not_verified.statement` entry. It is an indirect definition
context, not an unused source theorem, and is not moved into the proof list to
manufacture a direct proof dependency.

-/

namespace Hochschild1945

universe u

/-- **Corollary (p. 67)** (Hochschild). For each finite-dimensional extension,
Theorem 4.1 kills H¹ of the twisted module, Theorem 3.1 identifies it with H²,
and Theorem 6.1 gives segregation. These dependencies remain visible in the proof. -/
theorem separable_segregated_in_every_extension (K A : Type u)
    [Field K] [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    (h : sourceSeparable K A) : SegregatedInEveryExtension K A := by
  apply (segregated_iff_second_cohomology_vanishes K A).mpr
  intro P _ _ M
  letI := (separable_iff_first_cohomology_vanishes K A).mp h (A →ₗ[K] P) (twistedModule M)
  exact (dimensionShift M 0).injective.subsingleton

end Hochschild1945
