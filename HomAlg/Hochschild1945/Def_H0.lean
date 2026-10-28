import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_2_1

/-!
```yaml node
id: "Hochschild1945.Def_H0"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (footnote 6, p. 60)"
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
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
decls:
  - "Hochschild1945.degreeZeroGroup"
  - "Hochschild1945.degreeZeroGroup_eq_cocycles"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.degreeZeroGroup:
        statement_sha256: "dab674b50eed43ddcec47841cf733c57f3a471e3a88ab4e4501f1b7aa20e326f"
        type_hash: "0000000025462ced"
        meaning_hash: "f7b630fbf47cc7be"
      Hochschild1945.degreeZeroGroup_eq_cocycles:
        statement_sha256: "bda745d320c5a824a0126ff5f23b11f1dca155933fe62133b047f9d5d805c4f0"
        type_hash: "00000000ff90b36c"
        meaning_hash: "acbf0274740670f9"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Degree-zero cohomology"
```

## Statement

$H^0(\mathfrak{A},\mathfrak{P})$ is of no interest. We may define it as the
additive subgroup of $\mathfrak{P}$ consisting of all $u\in\mathfrak{P}$ such that
$a\cdot u=u\cdot a$, for all $a\in\mathfrak{A}$.

## Description

The degree-zero group from footnote 6 consists of elements on which both actions agree.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- **Definition (footnote 6, p. 60)**. The source's degree-zero group consists
of those module elements whose left and right actions agree for every algebra element. -/
def degreeZeroGroup : Submodule K P where
  carrier := {p | ∀ a : A, M.left a p = M.right p a}
  zero_mem' := by simp
  add_mem' := by intro p q hp hq a; simp [hp a, hq a]
  smul_mem' := by intro c p hp a; simp [hp a]

/-- The source footnote agrees with the kernel of its degree-zero coboundary. -/
theorem degreeZeroGroup_eq_cocycles : degreeZeroGroup M = cocycles M 0 := by
  ext p
  change (∀ a, M.left a p = M.right p a) ↔ delta M 0 p = 0
  constructor
  · intro h
    ext a
    simp only [delta]
    change M.left a p - M.right p a = 0
    exact sub_eq_zero.mpr (h a)
  · intro h a
    rw [delta] at h
    have ha := congrArg (fun f : A →ₗ[K] P => f a) h
    change M.left a p - M.right p a = 0 at ha
    exact sub_eq_zero.mp ha

end Hochschild1945
