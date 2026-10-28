import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Not_A_colon_P

/-!
```yaml node
id: "Hochschild1945.Con_bar_map"
doc: "Hochschild1945"
kind: "construction"
source:
  label: "Construction (unnumbered, p. 60)"
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
    - "Hochschild1945.Def_cochain"
  proof:
    - "Hochschild1945.Not_A_colon_P"
decls:
  - "Hochschild1945.barEquiv"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.barEquiv:
        statement_sha256: "be20ccf034e823637efa0f77603b6384caa124ca23eaaf8c0e339b6bea739d2e"
        type_hash: "00000000df18d29f"
        meaning_hash: "8fa90b680dbc940a"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Cochain dimension-shift map"
```

## Statement

Corresponding to any element $f$ of $(\mathfrak{A}^{(m)}:\mathfrak{P})$, $m\geqq 1$, we define
an element $\bar f\in(\mathfrak{A}^{(m-1)}:(\mathfrak{A}:\mathfrak{P}))$ by the relation
$\bar f\{a_1,\cdots,a_{m-1}\}\{a_m\}=f\{a_1,\cdots,a_m\}$.
(We identify $(\mathfrak{A}^{(0)}:(\mathfrak{A}:\mathfrak{P}))$ with $(\mathfrak{A}:\mathfrak{P})$).

## Description

The actual last-factor currying equivalence, including the source degree-one identification.
## Formalization notes

The source calls the target coefficient module `(A:P)`, so the authored proof dependency includes `Not_A_colon_P`. The bar-map equivalence itself only uses its underlying linear-map carrier; it does not inspect the special actions. Those actions enter `delta` and the commuting identity in Definition 2.1. This explains the source-only dependency in `deps_diff`.
-/

namespace Hochschild1945

open scoped TensorProduct

universe u

variable (K A P : Type u) [Field K] [AddCommGroup A] [Module K A]
  [AddCommGroup P] [Module K P]

/-- **Construction (unnumbered, p. 60)**. Currying the last Kronecker factor is
exactly the source's map `f ↦ f̄`, including its explicit degree-one identification. -/
def barEquiv : (n : Nat) → Cochain K A P (n + 1) ≃ₗ[K] Cochain K A (A →ₗ[K] P) n
  | 0 => LinearEquiv.refl K (A →ₗ[K] P)
  | n + 1 => (TensorProduct.lift.equiv (RingHom.id K) (KroneckerPower K A n) A P).symm

/-- On a pure tensor, the bar map evaluates exactly as in the original relation. -/
@[simp] theorem barEquiv_apply (n : Nat) (f : Cochain K A P (n + 2))
    (t : KroneckerPower K A n) (a : A) :
    barEquiv K A P (n + 1) f t a = f (t ⊗ₜ[K] a) := rfl

/-- The degree-one bar identification is the identity on linear maps. -/
@[simp] theorem barEquiv_zero (f : Cochain K A P 1) : barEquiv K A P 0 f = f := rfl

end Hochschild1945
