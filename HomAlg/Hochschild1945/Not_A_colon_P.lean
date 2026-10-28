import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Prop_1_1

/-!
```yaml node
id: "Hochschild1945.Not_A_colon_P"
doc: "Hochschild1945"
kind: "notation"
source:
  label: "Notation (unnumbered, p. 59)"
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
    - "Hochschild1945.Prop_1_1"
  proof: []
decls:
  - "Hochschild1945.AColonP"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.AColonP:
        statement_sha256: "16f07c179beb326ace7d046bc23e10a477d6ce443ad23b1d29d78f4c652aaecf"
        type_hash: "000000003991b2c6"
        meaning_hash: "a430e3fba47d6085"
    session: "ci-firstchapter-independent"
    author_session: "/root/lean_fixtures"
title: "Notation for the cochain module"
```

## Statement

When $(\mathfrak{A}^{(1)}:\mathfrak{P})$ is regarded as a two-sided $\mathfrak{A}$-module in this
particular fashion we denote it by $(\mathfrak{A}:\mathfrak{P})$.

## Description

The source construction is retained with an associative algebra without a required identity. Tensor products and linear maps supply basic linear algebra only; no existing cohomology construction is substituted.
-/


namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- **Notation (unnumbered, p. 59)**. `(A:P)` denotes the source's specially
constructed two-sided module, retaining both of its specific actions. -/
abbrev AColonP (M : TwoSidedModule K A P) : TwoSidedModule K A (A →ₗ[K] P) :=
  twistedModule M

end Hochschild1945
