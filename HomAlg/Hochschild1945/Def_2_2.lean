import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_1

/-!
```yaml node
id: "Hochschild1945.Def_2_2"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition 2.2"
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
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof: []
decls:
  - "Hochschild1945.IsCocycle"
  - "Hochschild1945.IsCoboundary"
  - "Hochschild1945.cocycles"
  - "Hochschild1945.coboundaries"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.IsCocycle:
        statement_sha256: "7961654ad22c0a57dd462e44dd4449c41141cd866f2793685267af09a6d65faf"
        type_hash: "0000000020265073"
        meaning_hash: "d6fc9a4f5bf96ded"
      Hochschild1945.IsCoboundary:
        statement_sha256: "ddb51f2071815236a5c774a56fb11d882ae802a718376f8dd72583dcb1ed093c"
        type_hash: "0000000004a6c6c3"
        meaning_hash: "36e252345439607d"
      Hochschild1945.cocycles:
        statement_sha256: "4339464d3479773f4dd9f58e88555d88179884e0387916b236bae6cbf110dba5"
        type_hash: "000000004b8fe61e"
        meaning_hash: "d2c6fe57a08ba4d8"
      Hochschild1945.coboundaries:
        statement_sha256: "8785874993879563733ef6cb59b3306048e732cd943a668e2d98a8ed101ce466"
        type_hash: "000000004b8fe61e"
        meaning_hash: "d2c6fe57a08ba4d8"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Cocycles and coboundaries"
```

## Statement

A cochain $f$ is called a cocycle if $\delta f=0$. $f$ is said to be a
coboundary if there exists a cochain $g$ such that $f=\delta g$.

## Description

Source cocycles are the kernel of the authored coboundary; positive-degree coboundaries are its image.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- **Definition 2.2**. A source cochain is a cocycle exactly when its coboundary vanishes. -/
def IsCocycle (n : Nat) (f : Cochain K A P n) : Prop := delta M n f = 0

/-- **Definition 2.2**. A positive-degree source cochain is a coboundary exactly
when it is the coboundary of a cochain in the preceding degree. -/
def IsCoboundary (n : Nat) (f : Cochain K A P (n + 1)) : Prop :=
  ∃ g : Cochain K A P n, f = delta M n g

/-- The linear subspace of all source cocycles, using the elementary kernel construction. -/
def cocycles (n : Nat) : Submodule K (Cochain K A P n) := LinearMap.ker (delta M n)

/-- The linear subspace of all source coboundaries. The degree-zero convention is
zero, so the quotient in degree zero agrees with the separate source footnote. -/
def coboundaries : (n : Nat) → Submodule K (Cochain K A P n)
  | 0 => ⊥
  | n + 1 => LinearMap.range (delta M n)

/-- The kernel subspace expresses exactly the source predicate. -/
theorem mem_cocycles (n : Nat) (f : Cochain K A P n) :
    f ∈ cocycles M n ↔ IsCocycle M n f := Iff.rfl

/-- The image subspace in positive degree expresses exactly the source predicate. -/
theorem mem_coboundaries (n : Nat) (f : Cochain K A P (n + 1)) :
    f ∈ coboundaries M (n + 1) ↔ IsCoboundary M n f := by
  change (∃ g, delta M n g = f) ↔ ∃ g, f = delta M n g
  exact exists_congr (fun _ => eq_comm)

end Hochschild1945
