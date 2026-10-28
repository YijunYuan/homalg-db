import Mathlib.RingTheory.TensorProduct.Basic
import Mathlib.LinearAlgebra.TensorProduct.Basis
import Mathlib.LinearAlgebra.FiniteDimensional.Defs
import Mathlib.Algebra.Ring.InjSurj
import Mathlib.Algebra.Algebra.Unitization
import Mathlib.RingTheory.Jacobson.Radical

/-!
```yaml node
id: "Hochschild1945.Def_separable"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 61)"
  pages:
    - 60
    - 61
  chapter: "4"
tags:
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement: []
  proof: []
decls:
  - "Hochschild1945.sourceSeparable"
  - "Hochschild1945.separableWithBasis"
  - "Hochschild1945.basisExtensionMul"
  - "Hochschild1945.Semisimple"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.sourceSeparable:
        statement_sha256: "340dd161dadb35e20773ad4b01ec9a65db8bf4f4bc8ccbf56b952012b088cf8f"
        type_hash: "0000000075880141"
        meaning_hash: "0000000075880141"
      Hochschild1945.separableWithBasis:
        statement_sha256: "e1316b2e914de0f5811d06298c5ffe785515eae2ce77bdd7802651d0336b1f22"
        type_hash: "000000006ae5a3ef"
        meaning_hash: "000000006ae5a3ef"
      Hochschild1945.basisExtensionMul:
        statement_sha256: "cd555f0fe88cf1d83515c2f70b4c97cca84e757cbacb0663ea12419ca8c81547"
        type_hash: "00000000c0e431e6"
        meaning_hash: "929393e214f9c757"
      Hochschild1945.Semisimple:
        statement_sha256: "4c14cb150acf7c1abc7405d48523834b032b7b902464b0dccaa45566631c6bad"
        type_hash: "0000000075880141"
        meaning_hash: "0000000075880141"
    session: "ci-separability-independent"
    author_session: "codex-schema-taxonomy-2026-10-28"
title: "Separable algebras"
mathlib:
  relation: "variant"
  decls:
    - "TensorProduct"
    - "Algebra.TensorProduct.tmul_mul_tmul"
  bridge: "Hochschild1945.Bridge_Def_separable_mathlib"
  note: "The bridge compares the chosen finite basis algebra with nonunital tensor multiplication. It
    does not identify arbitrary nonunital algebras with Algebra.IsSeparable."
```

## Statement

We recall that an algebra $\mathfrak{A}$ over the field $\Phi$ is said to be separable if
$\mathfrak{A}_\Gamma$ is semi-simple for every extension field $\Gamma$ of $\Phi$. Here,
$\mathfrak{A}_\Gamma$ denotes the algebra over $\Gamma$ which consists of all linear
combinations $\sum_{i=1}^n\gamma_i a_i$, where $\gamma_i\in\Gamma$ and where
$a_1$, $\cdots$, $a_n$ constitute a basis of $\mathfrak{A}$ over $\Phi$, multiplication
being derived from the multiplication of the $a_i$ in $\mathfrak{A}$ over
$\Phi$.\textsuperscript{7}

[Footnote 7] From here on we shall make use of the classical results in the
theory of separable algebras without giving specific references. The results in
question can be found in any of the standard expositions, such as: Deuring,
``\textit{Algebren}''; Van der Waerden, ``\textit{Moderne Algebra}''; or Jacobson,
loc. cit.

## Description

Defines separability by semisimplicity after every extension of the ground field, with scalar extension described using a basis.

## Formalization notes

The opening word is on printed page 60; the definition continues on page 61.
`BasisExtension n Γ` is the actual finite coefficient space `Fin n → Γ`.
Its additive and scalar operations are the ordinary coordinate operations; its
multiplication is transferred through the extended-basis coordinate map. The
bridge proves the full structure-constant formula, so the definition retains
the original multiplication rather than the unrelated pointwise product.
All structures on this space are named constructions installed only locally.

`separableWithBasis b` retains the selected basis as an argument.
`sourceSeparable K A` chooses `Module.finBasis K A`, exactly the choice of a finite
basis made in the source, and quantifies all field extensions in the ambient
universe. It makes no identity, characteristic, perfection, or algebraic-closure
assumption. The zero-dimensional algebra is not excluded.

The classical term "semi-simple" is represented by `Semisimple K A`, whose
finite-dimensional assumption is explicit. Its radical is the preimage of
`Ring.jacobson (Unitization K A)` under `Unitization.inr`; radical zero is the
classical semisimplicity boundary for finite-dimensional associative algebras.
This elementary background is proposed in the document's foundation registry;
no cohomology criterion or identity theorem is built into the definition.
-/

namespace Hochschild1945

universe u

open scoped TensorProduct

variable (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A]

/-- **Definition (unnumbered, p. 61)** (Hochschild), background term.
Semisimplicity in the finite-dimensional, possibly nonunital source setting:
the algebra has zero intersection with the Jacobson radical of its unitization.
No identity element in the original algebra is assumed. -/
def Semisimple [FiniteDimensional K A] : Prop :=
  ∀ a : A, Unitization.inr a ∈ Ring.jacobson (Unitization K A) → a = 0

variable {K A} {n : ℕ} (b : Module.Basis (Fin n) K A)
  (Γ : Type u) [Field Γ] [Algebra K Γ]

/-- Formal coefficient tuples, kept distinct from the pointwise product algebra. -/
def BasisExtension (n : ℕ) (Γ : Type u) := Fin n → Γ

/-- The coordinate space has its ordinary pointwise additive group. -/
noncomputable abbrev basisExtensionAddCommGroup : AddCommGroup (BasisExtension n Γ) :=
  inferInstanceAs (AddCommGroup (Fin n → Γ))

attribute [local instance] basisExtensionAddCommGroup

/-- The coordinate space has its ordinary coefficient-wise scalar action. -/
noncomputable abbrev basisExtensionModule : Module Γ (BasisExtension n Γ) :=
  inferInstanceAs (Module Γ (Fin n → Γ))

attribute [local instance] basisExtensionModule

/-- The source coordinate algebra has precisely the finite selected dimension. -/
noncomputable abbrev basisExtensionFiniteDimensional : FiniteDimensional Γ (BasisExtension n Γ) :=
  inferInstanceAs (FiniteDimensional Γ (Fin n → Γ))

attribute [local instance] basisExtensionFiniteDimensional

/-- The source's coefficient tuples represent the formal linear combinations of
the selected basis, after extending coefficients to Γ. -/
noncomputable def basisExtensionEquiv : (BasisExtension n Γ) ≃ₗ[Γ] Γ ⊗[K] A :=
  (b.baseChange Γ).equivFun.symm

/-- Multiplication on the actual coefficient space, induced by multiplication
of the selected source basis; its structure-constant formula is proved below. -/
noncomputable def basisExtensionMul (x y : BasisExtension n Γ) : BasisExtension n Γ :=
  (basisExtensionEquiv b Γ).symm (basisExtensionEquiv b Γ x * basisExtensionEquiv b Γ y)

/-- Associativity and distributivity transfer to the source coefficient space.
The pointwise additive structure is retained, but multiplication is not pointwise. -/
noncomputable abbrev basisExtensionRing : NonUnitalRing (BasisExtension n Γ) := by
  letI : Mul (BasisExtension n Γ) := ⟨basisExtensionMul b Γ⟩
  let e := basisExtensionEquiv b Γ
  exact Function.Injective.nonUnitalRing e e.injective e.map_zero e.map_add
    (fun x y => e.apply_symm_apply _) e.map_neg e.map_sub
    (fun m x => map_nsmul e m x) (fun m x => map_zsmul e m x)

/-- Left Γ-linearity of source multiplication, supplied only as a local instance. -/
noncomputable abbrev basisExtensionScalarTower :
    letI := basisExtensionRing b Γ
    IsScalarTower Γ (BasisExtension n Γ) (BasisExtension n Γ) := by
  let _ := basisExtensionRing b Γ
  constructor
  intro r x y
  change basisExtensionMul b Γ (r • x) y = r • basisExtensionMul b Γ x y
  apply (basisExtensionEquiv b Γ).injective
  simp only [basisExtensionMul, LinearEquiv.apply_symm_apply, map_smul, smul_mul_assoc]

/-- Right Γ-linearity of source multiplication, supplied only as a local instance. -/
noncomputable abbrev basisExtensionSmulComm :
    letI := basisExtensionRing b Γ
    SMulCommClass Γ (BasisExtension n Γ) (BasisExtension n Γ) := by
  let _ := basisExtensionRing b Γ
  constructor
  intro r x y
  change r • basisExtensionMul b Γ x y = basisExtensionMul b Γ x (r • y)
  apply (basisExtensionEquiv b Γ).injective
  simp only [basisExtensionMul, LinearEquiv.apply_symm_apply, map_smul, mul_smul_comm]

/-- The source separability condition with the choice of finite basis explicit. -/
def separableWithBasis : Prop :=
  ∀ (Γ : Type u) [Field Γ] [Algebra K Γ],
    letI := basisExtensionRing b Γ
    letI := basisExtensionScalarTower b Γ
    letI := basisExtensionSmulComm b Γ
    Semisimple Γ (BasisExtension n Γ)

/-- **Definition (unnumbered, p. 61)** (Hochschild). Every field extension makes
the algebra of formal linear combinations of a selected finite basis semisimple. -/
def sourceSeparable (K A : Type u) [Field K] [NonUnitalRing A] [Module K A]
    [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A] : Prop :=
  separableWithBasis (Module.finBasis K A)

end Hochschild1945
