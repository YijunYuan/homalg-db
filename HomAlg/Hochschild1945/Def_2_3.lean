import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Lem_cocycle_subgroups
import HomAlg.Hochschild1945.Def_2_2
import Mathlib.LinearAlgebra.Quotient.Basic

/-!
```yaml node
id: "Hochschild1945.Def_2_3"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition 2.3"
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
    - "Hochschild1945.Lem_cocycle_subgroups"
decls:
  - "Hochschild1945.cohomologySpace"
  - "Hochschild1945.Cohomology"
  - "Hochschild1945.boundariesInCycles"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.cohomologySpace:
        statement_sha256: "2fe29c5d12219155ae95aefb75cea8329960f65c7d605954fa644167c886fa0e"
        type_hash: "00000000c6f53c17"
        meaning_hash: "afa6b7aeddcabb44"
      Hochschild1945.Cohomology:
        statement_sha256: "e73b2e74e435ddfccec653e0709e6d99d5db88b5094ec45ee848e6eec99bf172"
        type_hash: "000000004ad51892"
        meaning_hash: "0c9c3c0c402103b1"
      Hochschild1945.boundariesInCycles:
        statement_sha256: "fb1d170d86f6397159cd8a4c6d1bbf562c9997a3b503654f1e4f88b80f2d696b"
        type_hash: "000000002c03f5fd"
        meaning_hash: "099670bc57839784"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Cohomology groups"
```

## Statement

For $m\geqq 1$, the $m$-dimensional cohomology group of $\mathfrak{A}$ for the module
$\mathfrak{P}$, denoted by $H^m(\mathfrak{A},\mathfrak{P})$, is the group of the $(m,\mathfrak{P})$-cocycles
of $\mathfrak{A}$, modulo the subgroup of coboundaries.\textsuperscript{6}

## Description

The source cohomology group is the actual quotient of cocycles by the included coboundaries.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- Include actual coboundaries in cocycles using the source's proved square-zero law. -/
def boundaryInclusion (n : Nat) : coboundaries M n →ₗ[K] cocycles M n :=
  (coboundaries M n).subtype.codRestrict (cocycles M n)
    (fun f => coboundaries_le_cocycles M n f.property)

/-- The image of the proved boundary inclusion, regarded as a subgroup of cocycles. -/
def boundariesInCycles (n : Nat) : Submodule K (cocycles M n) :=
  LinearMap.range (boundaryInclusion M n)

/-- The subgroup of cocycles identifies exactly the original boundaries. -/
@[simp] theorem mem_boundariesInCycles (n : Nat) (f : cocycles M n) :
    f ∈ boundariesInCycles M n ↔ (f : Cochain K A P n) ∈ coboundaries M n := by
  constructor
  · rintro ⟨b, rfl⟩
    exact b.property
  · intro hf
    exact ⟨⟨f, hf⟩, rfl⟩

/-- **Definition 2.3**. The source cohomology space is literally the cocycle
space modulo its boundary subspace, rather than an existing cohomology implementation. -/
def cohomologySpace (n : Nat) : ModuleCat.{u} K :=
  ModuleCat.of K ((cocycles M n) ⧸ boundariesInCycles M n)

/-- The underlying source cohomology group; its operations are the quotient operations. -/
abbrev Cohomology (n : Nat) : Type u := cohomologySpace M n

end Hochschild1945
