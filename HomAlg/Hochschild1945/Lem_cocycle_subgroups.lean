import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Lem_delta_delta_zero

/-!
```yaml node
id: "Hochschild1945.Lem_cocycle_subgroups"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Lemma (unnumbered, p. 60, 2)"
  pages:
    - 60
  chapter: "2"
tags:
  - "cochain-complex"
  - "cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Lem_delta_delta_zero"
decls:
  - "Hochschild1945.coboundaries_le_cocycles"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.coboundaries_le_cocycles:
        statement_sha256: "3464b926d14ac86fb5da8f73a30e9e73b7f057aabb8915e2d4b3ff02abfee821"
        type_hash: "0000000083ceb7a7"
        meaning_hash: "ecda1e9a9cc23628"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Subgroups of cocycles and coboundaries"
```

## Statement

Clearly, the set of $(m,\mathfrak{P})$-cocycles of $\mathfrak{A}$ constitutes a subgroup of the
additive group of the $(m,\mathfrak{P})$-cochains of $\mathfrak{A}$. By the last result, the set
of coboundaries constitutes a subgroup of the corresponding group of cocycles.

## Proof

By the last result, the set of coboundaries constitutes a subgroup of the corresponding group of cocycles.

[uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Lem_delta_delta_zero`]

## Description

The coboundary subgroup lies in the cocycle subgroup by the source square-zero lemma.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- **Lemma (unnumbered, p. 60, 2)**. The subspace of coboundaries lies in the
subspace of cocycles. For a boundary represented by `δg`, this is precisely `δ²g=0`,
as in the original proof; both subspaces carry their induced additive groups. -/
theorem coboundaries_le_cocycles (n : Nat) : coboundaries M n ≤ cocycles M n := by
  cases n with
  | zero => exact bot_le
  | succ n =>
      rintro f ⟨g, rfl⟩
      exact delta_delta_zero M n g

end Hochschild1945
