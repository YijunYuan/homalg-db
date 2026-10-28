import HomAlg.Hochschild1945.Def_separable

/-!
```yaml node
id: "Hochschild1945.Bridge_Def_separable_mathlib"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Bridge for Def_separable"
  pages:
    - 61
  chapter: "4"
tags:
  - "bridge"
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
  proof:
    - "Hochschild1945.Def_separable"
decls:
  - "Hochschild1945.basisExtension_tensor_equivalence"
  - "Hochschild1945.basisExtensionMul_coordinates"
  - "Hochschild1945.basisExtensionMul_basis"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.basisExtension_tensor_equivalence:
        statement_sha256: "dec752f36d958a16666eb42a2ccf803253f3c5e1c4dfa25ccb188959701f6127"
        type_hash: "0000000010e99246"
        meaning_hash: "df845de0bba3398f"
      Hochschild1945.basisExtensionMul_coordinates:
        statement_sha256: "e0e7510fcba2bd2bb1ce25432eafd36376350034cb471cccc3e7fa14aa63b592"
        type_hash: "00000000bea5a618"
        meaning_hash: "164dc1afdaa84349"
      Hochschild1945.basisExtensionMul_basis:
        statement_sha256: "ecfdaa73855a8cc13629204f33c8267713d90ce6eeb1e8d34a238536812fd4cf"
        type_hash: "00000000d380c38b"
        meaning_hash: "43674313e7812a96"
    session: "ci-separability-independent"
    author_session: "codex-schema-taxonomy-2026-10-28"
title: "Basis scalar extension and the nonunital tensor product"
nl_proof_source:
  follows: "agent"
aux:
  parent: "Hochschild1945.Def_separable"
  kind: "bridge"
  reason: "Identify the original finite basis extension, including its multiplication, with the nonunital
    tensor-product algebra."
```

## Statement

[Editorial bridge] For a selected basis $a_1,\ldots,a_n$, the source coefficient
space is linearly equivalent to $\Gamma\otimes_\Phi\mathfrak A$. The equivalence
sends a tuple $(\gamma_i)$ to $\sum_i\gamma_i(1\otimes a_i)$ and preserves
multiplication. Its multiplication has the original structure constants:
$$(xy)_k=\sum_i\sum_j x_i y_j\,\iota(c_{ijk}),\qquad
  a_i a_j=\sum_k c_{ijk}a_k.$$
No unit in the source algebra is assumed.

## Proof

Extend the selected basis to the tensor product and use its coordinate
isomorphism. Each elementary coefficient tuple maps to the corresponding
elementary tensor. Tensor multiplication sends
$(1\otimes a_i)(1\otimes a_j)$ to $1\otimes(a_i a_j)$, whose coordinates are
the embedded original structure constants. Bilinearity and the finite basis
expansions give the formula for arbitrary tuples. Thus this is an equivalence
of the actual source multiplication, not only of the underlying vector spaces.
[uses `Hochschild1945.Def_separable`]

## Description

Proves the scalar-extension construction agrees with Mathlib tensor multiplication, including its full coordinate product formula.

## Formalization notes


The `mathlib-bypass-proof` warning matches the type constructor TensorProduct,
which is the explicit comparison target of this bridge and an approved linear
algebra foundation. The proof constructs the coefficient equivalence and proves
its multiplication and structure-constant formulas from the source basis.
It does not import a Mathlib separability criterion or replace a source lemma.
Both the source dependency and its Mathlib correspondence remain recorded;
the warning remains visible for this intentional bridge use.

-/

namespace Hochschild1945

universe u

open scoped TensorProduct

variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A]
  {n : ℕ} (b : Module.Basis (Fin n) K A) (Γ : Type u) [Field Γ] [Algebra K Γ]

attribute [local instance] basisExtensionAddCommGroup basisExtensionModule

omit [SMulCommClass K A A] [IsScalarTower K A A] in
/-- Coordinate tuples give exactly the formal finite linear combinations in the source. -/
theorem basisExtensionEquiv_apply (x : BasisExtension n Γ) :
    basisExtensionEquiv b Γ x = ∑ i, x i • (1 ⊗ₜ[K] b i) := by
  change (b.baseChange Γ).equivFun.symm (show Fin n → Γ from x) = _
  rw [Module.Basis.equivFun_symm_apply]
  simp only [Module.Basis.baseChange_apply]

omit [SMulCommClass K A A] [IsScalarTower K A A] in
/-- The source basis vector with coefficient one maps to its elementary tensor. -/
theorem basisExtensionEquiv_basis (i : Fin n) :
    basisExtensionEquiv b Γ (Pi.single i 1) = 1 ⊗ₜ[K] b i := by
  change (b.baseChange Γ).equivFun.symm (Pi.single i 1) = _
  rw [Module.Basis.equivFun_symm_apply]
  simp [Pi.single_apply]

/-- Multiplication of two source basis vectors retains the original structure constants. -/
theorem basisExtensionMul_basis (i j k : Fin n) :
    basisExtensionMul b Γ (Pi.single i 1) (Pi.single j 1) k =
      algebraMap K Γ (b.repr (b i * b j) k) := by
  change (b.baseChange Γ).equivFun
    (basisExtensionEquiv b Γ (Pi.single i 1) * basisExtensionEquiv b Γ (Pi.single j 1)) k = _
  rw [basisExtensionEquiv_basis, basisExtensionEquiv_basis]
  simp [Algebra.smul_def]

/-- The complete original coordinate product formula for arbitrary finite linear combinations. -/
theorem basisExtensionMul_coordinates (x y : BasisExtension n Γ) (k : Fin n) :
    basisExtensionMul b Γ x y k =
      ∑ i, ∑ j, x i * y j * algebraMap K Γ (b.repr (b i * b j) k) := by
  change (b.baseChange Γ).equivFun (basisExtensionEquiv b Γ x * basisExtensionEquiv b Γ y) k = _
  rw [basisExtensionEquiv_apply, basisExtensionEquiv_apply]
  simp [Finset.sum_mul, Finset.mul_sum, smul_mul_assoc, mul_smul_comm,
    Algebra.smul_def, mul_assoc, mul_comm, mul_left_comm]
  rw [Finset.sum_comm]

/-- **Bridge for Definition (unnumbered, p. 61)** (Hochschild). There is an actual Γ-linear equivalence
from the source's finite coefficient algebra to the tensor-product algebra, and it
preserves the multiplication determined by the original basis products. -/
theorem basisExtension_tensor_equivalence :
    ∃ e : BasisExtension n Γ ≃ₗ[Γ] Γ ⊗[K] A,
      ∀ x y, e (basisExtensionMul b Γ x y) = e x * e y := by
  exact ⟨basisExtensionEquiv b Γ, fun x y => (basisExtensionEquiv b Γ).apply_symm_apply _⟩

end Hochschild1945
