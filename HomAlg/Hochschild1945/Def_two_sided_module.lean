import Mathlib.Algebra.Algebra.Bilinear
import Mathlib.LinearAlgebra.FiniteDimensional.Defs

/-!
```yaml node
id: "Hochschild1945.Def_two_sided_module"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 59, 1)"
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
  statement: []
  proof: []
decls:
  - "Hochschild1945.TwoSidedModule"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.TwoSidedModule:
        statement_sha256: "c08396d606c61b6cccd0938b9531afad51ba4db600e3dc2630c6d45a60b6fefc"
        type_hash: "000000005e6b1cbb"
        meaning_hash: "000000005e6b1cbb"
    session: "ci-firstchapter-independent"
    author_session: "/root/lean_fixtures"
title: "Two-sided modules"
mathlib:
  relation: "variant"
  decls:
    - "NonUnitalAlgHom"
  bridge: "Hochschild1945.Bridge_Def_two_sided_module_mathlib"
  note: "The bridge identifies both source actions with commuting nonunital algebra representations on
    Module.End, using the opposite algebra for the right action. No unital action is imposed."
```

## Statement

Let $\mathfrak{A}$ be an associative algebra, over an arbitrary field $\Phi$. We consider
linear spaces $\mathfrak{P}$ over $\Phi$ which are at the same time $\mathfrak{A}$-left modules
and $\mathfrak{A}$-right modules\textsuperscript{4}. If $a\in\mathfrak{A}$ we denote the
corresponding $\Phi$-endomorphisms\textsuperscript{5} of $\mathfrak{P}$ by
$u\to a\cdot u$, $u\to u\cdot a$ respectively. In addition to the usual
requirements on these operations for one-sided modules we demand that, if
$a_1$, $a_2\in\mathfrak{A}$ and $u\in\mathfrak{P}$,
$(a_1\cdot u)\cdot a_2=a_1\cdot(u\cdot a_2)$. Then $\mathfrak{P}$ is called a
two-sided $\mathfrak{A}$-module.

## Description

The source construction is retained with an associative algebra without a required identity. Tensor products and linear maps supply basic linear algebra only; no existing cohomology construction is substituted.
-/


namespace Hochschild1945

universe u

/-- **Definition (unnumbered, p. 59, 1)**. The two bilinear actions and the three
associativity identities in the source definition. No identity is required in the algebra. -/
structure TwoSidedModule (K A P : Type u) [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
    [FiniteDimensional K A] [AddCommGroup P] [Module K P] where
  /-- Left multiplication, linear in the algebra element and in the module element. -/
  left : A →ₗ[K] P →ₗ[K] P
  /-- Right multiplication, linear in the module element and in the algebra element. -/
  right : P →ₗ[K] A →ₗ[K] P
  /-- Associativity of the left module action. -/
  left_assoc : ∀ a b p, left (a * b) p = left a (left b p)
  /-- Associativity of the right module action. -/
  right_assoc : ∀ p a b, right (right p a) b = right p (a * b)
  /-- Compatibility of the two module actions. -/
  left_right : ∀ a p b, right (left a p) b = left a (right p b)

end Hochschild1945
