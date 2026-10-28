import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Aux_Def_extension_section
import HomAlg.Hochschild1945.Def_natural_homomorphism
import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas
import Mathlib.Algebra.Algebra.Operations
import Mathlib.Algebra.Group.Pointwise.Set.ListOfFn
import Mathlib.Algebra.Module.Submodule.Bilinear
import Mathlib.LinearAlgebra.Quotient.Bilinear
import Mathlib.Algebra.Algebra.Bilinear
import Mathlib.Algebra.Ring.InjSurj
import HomAlg.Hochschild1945.Cited_semisimple_ideal_structure
import HomAlg.Hochschild1945.Cited_radical_structure
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Lem_semisimple_ideal_summand

/-!
```yaml node
id: "Hochschild1945.Prop_6_1"
doc: "Hochschild1945"
kind: "proposition"
source:
  label: "Proposition 6.1"
  pages:
    - 64
    - 65
  chapter: "6"
tags:
  - "algebra-extension"
  - "segregated-extension"
  - "singular-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_extension"
  proof:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Aux_Def_extension_section"
    - "Hochschild1945.Def_natural_homomorphism"
    - "Hochschild1945.Lem_semisimple_ideal_summand"
    - "Hochschild1945.Cited_radical_structure"
    - "Hochschild1945.Cited_semisimple_ideal_structure"
decls:
  - "Hochschild1945.segregatedInEveryExtension_of_singular"
fidelity:
  status: "deviates"
  deviations:
    - kind: "generality"
      what: "Both universal extension predicates quantify finite-dimensional extension algebras B."
      why: "The source's proof uses nilpotence of the finite-dimensional radical and induction on the
        finite kernel dimension; unrestricted infinite-dimensional extensions do not satisfy the same
        assertion."
    - kind: "proof-route"
      what: "Complement the image of the kernel directly in B/R and pull the complement back, skipping
        the intermediate quotient B/(ker σ ∩ R)."
      why: "The actual pulled-back extension is surjective onto A and has kernel ker σ ∩ R; this proves
        the same nilpotent reduction with fewer quotient-transport constructions. The subsequent kernel-dimension
        induction follows the printed route."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.segregatedInEveryExtension_of_singular:
        statement_sha256: "7f9db4aaf7c42c4396fc44e9efc8d2fcc82be75c1d5858a19c2aac368daf7bdf"
        type_hash: "00000000434b76bf"
        meaning_hash: "de56c5d872330b43"
    session: "root-prop61-independent"
    author_session: "/root/ci_governance"
title: "Reduction to singular extensions"
```

## Statement

If $\mathfrak{A}$ is segregated in every singular extension then $\mathfrak{A}$ is segregated in every extension.

## Proof

We shall show first that we can reduce the problem to the case where the kernel $\mathfrak{K}$ of the extension is nilpotent. Specifically, we suppose that $\mathfrak{A}$ is segregated in every extension with nilpotent kernel and prove that then $\mathfrak{A}$ is segregated in every extension.

Let $\{\mathfrak{B},\sigma\}$ be any extension of $\mathfrak{A}$, let $\mathfrak{K}$ denote the kernel of the homomorphism $\sigma$, and let $\mathfrak{R}$ denote the radical of $\mathfrak{B}$. Consider $\mathfrak{B}/\mathfrak{R}$: clearly, $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$ is an ideal of $\mathfrak{B}/\mathfrak{R}$ (for $\mathfrak{K}$ is an ideal of $\mathfrak{B}$). Since $\mathfrak{B}/\mathfrak{R}$ is semi-simple (we need not consider the case where $\mathfrak{B}$, and hence also $\mathfrak{K}$, is nilpotent), so is $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$. [uses `Hochschild1945.Cited_semisimple_ideal_structure`] Further, $(\mathfrak{K}+\mathfrak{R})/\mathfrak{R}$ is isomorphic with $\mathfrak{K}/\mathfrak{N}$, where $\mathfrak{N}=\mathfrak{K}\cap\mathfrak{R}$. Obviously, $\mathfrak{N}$ is a nilpotent ideal of $\mathfrak{B}$, [uses `Hochschild1945.Cited_radical_structure`] $\mathfrak{K}/\mathfrak{N}$ is a semi-simple ideal of $\mathfrak{B}/\mathfrak{N}$, and we have the isomorphisms $\mathfrak{A}\cong\mathfrak{B}/\mathfrak{K}\cong(\mathfrak{B}/\mathfrak{N})/(\mathfrak{K}/\mathfrak{N})$.

Now, if $\mathfrak{C}$ is any algebra and $\mathfrak{S}$ a semi-simple ideal of $\mathfrak{C}$ then $\mathfrak{C}$ is the direct sum of $\mathfrak{S}$ and another ideal $\mathfrak{T}$. For, if $\mathfrak{H}$ is the radical of $\mathfrak{C}$ we have $\mathfrak{S}\cap\mathfrak{H}=\{0\}$; $\mathfrak{C}/\mathfrak{H}$ is semi-simple and contains the semi-simple ideal $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}\cong\mathfrak{S}$. Hence $\mathfrak{C}/\mathfrak{H}$ is the direct sum of $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}$ and another ideal $\mathfrak{U}$. Clearly, there exists an ideal $\mathfrak{T}\ (\supset\mathfrak{H})$ of $\mathfrak{C}$ such that $\mathfrak{U}=\mathfrak{T}/\mathfrak{H}$. Since $\mathfrak{U}\cap(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}=\{0\}$ we have $\mathfrak{T}\cap\mathfrak{S}\subset\mathfrak{H}$, and since $\mathfrak{S}\cap\mathfrak{H}=\{0\}$ this implies that $\mathfrak{T}\cap\mathfrak{S}=\{0\}$. Thus, $\mathfrak{C}$ is the direct sum of $\mathfrak{S}$ and $\mathfrak{T}$. [uses `Hochschild1945.Lem_semisimple_ideal_summand`]

Applying this to the above we conclude that there exists an ideal $\bar{\mathfrak{D}}$ of $\mathfrak{B}/\mathfrak{N}$ such that $\mathfrak{A}\cong\bar{\mathfrak{D}}$. But $\bar{\mathfrak{D}}$ is of the form $\mathfrak{D}/\mathfrak{N}$, where $\mathfrak{D}$ is an ideal of $\mathfrak{B}$, and there is a homomorphism of $\mathfrak{D}$ onto $\mathfrak{A}$ with the nilpotent kernel $\mathfrak{N}$. By hypothesis, there exists a subalgebra $\mathfrak{A}^*$ of $\mathfrak{D}$ such that $\mathfrak{A}^*\cong\mathfrak{A}$ and $\mathfrak{D}$ is the direct sum of $\mathfrak{N}$ and $\mathfrak{A}^*$. Obviously, $\mathfrak{A}^*$ is also a subalgebra of $\mathfrak{B}$, and $\mathfrak{B}$ is the direct sum of $\mathfrak{K}$ and $\mathfrak{A}^*$, i.e. $\mathfrak{A}$ is segregated in $\{\mathfrak{B},\sigma\}$.

It remains to show that if $\mathfrak{A}$ is segregated in every singular extension then $\mathfrak{A}$ is segregated in every extension whose kernel is nilpotent. This we prove by an induction on the dimension of the kernel. If the kernel is of dimension 0, $\mathfrak{B}$ is isomorphic with $\mathfrak{A}$ and there is nothing to prove. Suppose now that the dimension of the nilpotent kernel is $n$, and that our result has already been established for all extensions with a nilpotent kernel of dimension less than $n$. The homomorphism $\sigma$ of $\mathfrak{B}$ onto $\mathfrak{A}$ induces a homomorphism $\bar\sigma$ of $\mathfrak{B}/\mathfrak{K}^2$ onto $\mathfrak{A}$ whose kernel is $\mathfrak{K}/\mathfrak{K}^2$, so that $\{\mathfrak{B}/\mathfrak{K}^2,\bar\sigma\}$ is a singular extension of $\mathfrak{A}$. Hence there exists a subalgebra $\bar{\mathfrak{A}}$ of $\mathfrak{B}/\mathfrak{K}^2$ such that $\bar{\mathfrak{A}}\cong\mathfrak{A}$ and $\mathfrak{B}/\mathfrak{K}^2$ is the direct sum of $\mathfrak{K}/\mathfrak{K}^2$ and $\bar{\mathfrak{A}}$. Let $\mathfrak{C}$ be the subalgebra of $\mathfrak{B}$ such that $\mathfrak{C}/\mathfrak{K}^2=\bar{\mathfrak{A}}$. Then there exists a homomorphism $\sigma$ of $\mathfrak{C}$ onto $\mathfrak{A}$ whose kernel is $\mathfrak{K}^2$. Since $\mathfrak{K}$ is nilpotent, $\dim(\mathfrak{K}^2)<n$, and it follows from our inductive hypothesis that there exists a subalgebra $\mathfrak{A}^*$ of $\mathfrak{C}$ such that $\mathfrak{A}^*\cong\mathfrak{A}$ and $\mathfrak{C}$ is the direct sum of $\mathfrak{K}^2$ and $\mathfrak{A}^*$. Clearly, $\mathfrak{A}^*$ is also a subalgebra of $\mathfrak{B}$ and $\mathfrak{B}$ is the direct sum of $\mathfrak{K}$ and $\mathfrak{A}^*$. This completes the proof of Proposition 6.1.

[uses `Hochschild1945.Aux_Def_extension_section`] [uses `Hochschild1945.Def_natural_homomorphism`] [uses `Hochschild1945.Def_separable`]

## Description

Reduces segregation in finite-dimensional extensions to segregation in singular extensions using nilpotent kernels.

## Formalization notes

The extension definition itself remains valid for arbitrary B and arbitrary coefficient spaces P. Here both universal predicates explicitly quantify finite-dimensional B. This scope clarification is necessary for the printed proof on pp. 64–65, which invokes the finite-dimensional radical and inducts on the dimension of the nilpotent kernel. It is recorded as an explained generality deviation rather than silently labeling an unrestricted assertion faithful. The local proof is complete, relative to the separately declared classical cited results. The radical reduction complements the actual image of ker σ in B/R and pulls the complement back; its surjectivity and nilpotent kernel are proved explicitly. This skips the source's intermediate B/(ker σ ∩ R), and is recorded as a proof-route deviation.

The nilpotent step follows the source induction on the dimension of the kernel. Quotient multiplication is descended from the actual bilinear multiplication, the quotient map and its universal lift are proved, and the quotient by the kernel square is singular. Pulling a section back gives a new extension whose kernel embeds into the square. A nonzero nilpotent ideal strictly contains its square, so the new kernel has smaller dimension. Its nilpotence follows through the actual injective inclusion. The zero-kernel case uses the inverse of the original bijective algebra map.

`positivePower I n` denotes I to exponent n+1; thus `IsNilpotentIdeal` means some positive power is zero. Its connection to the source's finite products in the unitization is proved using actual multiplication and the cited radical nilpotence statement. Every source carrier instance introduced for the quotient is a named constructor installed only locally. No new axiom or local `sorry` is introduced.
-/

namespace Hochschild1945

universe u

variable (K A : Type u) [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]

/-- The source assertion that every extension of the algebra is segregated.
All extension algebras are finite-dimensional and need not have an identity. -/
def SegregatedInEveryExtension : Prop :=
  ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
    [IsScalarTower K B B] [FiniteDimensional K B],
    ∀ E : Extension K A B, E.IsSegregated

/-- The hypothesis in Proposition 6.1 restricts only to singular extensions. -/
def SegregatedInEverySingularExtension : Prop :=
  ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
    [IsScalarTower K B B] [FiniteDimensional K B],
    ∀ E : Extension K A B, E.IsSingular → E.IsSegregated

end Hochschild1945

namespace Hochschild1945.AlgebraIdeal
universe u
variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A]

/-- The vector-space quotient underlying the nonunital algebra quotient. -/
abbrev Quotient (I : AlgebraIdeal K A) := A ⧸ I.subalgebra.toSubmodule

/-- The source product modulo an ideal is bilinear in both quotient arguments. -/
def quotientBilinear (I : AlgebraIdeal K A) :
    I.Quotient →ₗ[K] I.Quotient →ₗ[K] I.Quotient :=
  ((LinearMap.mul K A).compr₂ I.subalgebra.toSubmodule.mkQ).liftQ₂
    I.subalgebra.toSubmodule I.subalgebra.toSubmodule
    (by
      intro a ha
      apply LinearMap.ext
      intro b
      apply (Submodule.Quotient.mk_eq_zero I.subalgebra.toSubmodule).mpr
      exact I.mul_mem_right b a ha)
    (by
      intro b hb
      apply LinearMap.ext
      intro a
      apply (Submodule.Quotient.mk_eq_zero I.subalgebra.toSubmodule).mpr
      exact I.mul_mem_left a b hb)

/-- Quotient multiplication, installed only in this module or by consumers. -/
abbrev quotientMul (I : AlgebraIdeal K A) : Mul I.Quotient := ⟨fun x y => I.quotientBilinear x y⟩
attribute [local instance] quotientMul

/-- The quotient map preserves multiplication by construction. -/
@[simp] theorem quotient_mk_mul (I : AlgebraIdeal K A) (a b : A) :
    I.subalgebra.toSubmodule.mkQ (a * b) =
      I.subalgebra.toSubmodule.mkQ a * I.subalgebra.toSubmodule.mkQ b := rfl

/-- The associative distributive quotient ring uses the actual quotient product. -/
abbrev quotientRing (I : AlgebraIdeal K A) : NonUnitalRing I.Quotient :=
  I.subalgebra.toSubmodule.mkQ_surjective.nonUnitalRing
    I.subalgebra.toSubmodule.mkQ (map_zero _) (map_add _) (I.quotient_mk_mul)
    (map_neg _) (map_sub _) (fun n a => map_nsmul _ n a) (fun n a => map_zsmul _ n a)
attribute [local instance] quotientRing

/-- Scalar multiplication commutes with the actual quotient product. -/
abbrev quotientSMulComm (I : AlgebraIdeal K A) : SMulCommClass K I.Quotient I.Quotient where
  smul_comm r x y := by
    change r • I.quotientBilinear x y = I.quotientBilinear x (r • y)
    exact (map_smul (I.quotientBilinear x) r y).symm

/-- The quotient product is compatible with scaling its left factor. -/
abbrev quotientScalarTower (I : AlgebraIdeal K A) : IsScalarTower K I.Quotient I.Quotient where
  smul_assoc r x y := by
    change I.quotientBilinear (r • x) y = r • I.quotientBilinear x y
    rw [map_smul]
    rfl

attribute [local instance] quotientSMulComm quotientScalarTower

/-- The actual surjective nonunital algebra quotient map. -/
def quotientMap (I : AlgebraIdeal K A) : A →ₙₐ[K] I.Quotient where
  toFun := I.subalgebra.toSubmodule.mkQ
  map_zero' := map_zero _
  map_add' := map_add _
  map_smul' := map_smul _
  map_mul' := I.quotient_mk_mul

/-- Membership in the actual ideal is exactly the quotient kernel. -/
@[simp] theorem quotientMap_eq_zero (I : AlgebraIdeal K A) (a : A) :
    I.quotientMap a = 0 ↔ a ∈ I.subalgebra :=
  Submodule.Quotient.mk_eq_zero I.subalgebra.toSubmodule

/-- Every quotient element has a representative in the original algebra. -/
theorem quotientMap_surjective (I : AlgebraIdeal K A) : Function.Surjective I.quotientMap :=
  I.subalgebra.toSubmodule.mkQ_surjective

variable {B : Type u} [NonUnitalRing B] [Module K B]
  [SMulCommClass K B B] [IsScalarTower K B B]

/-- A homomorphism killing an ideal descends to its actual quotient algebra. -/
def quotientLift (I : AlgebraIdeal K A) (f : A →ₙₐ[K] B)
    (hf : ∀ a ∈ I.subalgebra, f a = 0) : I.Quotient →ₙₐ[K] B where
  toFun := I.subalgebra.toSubmodule.liftQ (LinearMap.ofClass f) hf
  map_zero' := map_zero _
  map_add' := map_add _
  map_smul' := map_smul _
  map_mul' := by
    intro x y
    obtain ⟨a, rfl⟩ := I.quotientMap_surjective x
    obtain ⟨b, rfl⟩ := I.quotientMap_surjective y
    change I.subalgebra.toSubmodule.liftQ (LinearMap.ofClass f) hf
      (I.subalgebra.toSubmodule.mkQ a * I.subalgebra.toSubmodule.mkQ b) = _
    rw [← I.quotient_mk_mul]
    exact f.map_mul a b

omit [SMulCommClass K B B] [IsScalarTower K B B] in
/-- The descended homomorphism has its defining representative values. -/
@[simp] theorem quotientLift_apply (I : AlgebraIdeal K A) (f : A →ₙₐ[K] B)
    (hf : ∀ a ∈ I.subalgebra, f a = 0) (a : A) :
    I.quotientLift f hf (I.quotientMap a) = f a := rfl

omit [SMulCommClass K B B] [IsScalarTower K B B] in
/-- A surjective homomorphism remains surjective after descent. -/
theorem quotientLift_surjective (I : AlgebraIdeal K A) (f : A →ₙₐ[K] B)
    (hf : ∀ a ∈ I.subalgebra, f a = 0) (hs : Function.Surjective f) :
    Function.Surjective (I.quotientLift f hf) := by
  intro b
  obtain ⟨a, rfl⟩ := hs b
  exact ⟨I.quotientMap a, rfl⟩

end Hochschild1945.AlgebraIdeal
namespace Hochschild1945.AlgebraIdeal
universe u
variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A]

/-- The vector space spanned by all products from two actual ideals. -/
def productSpace (I J : AlgebraIdeal K A) : Submodule K A :=
  Submodule.map₂ (LinearMap.mul K A) I.subalgebra.toSubmodule J.subalgebra.toSubmodule

/-- Products of two ideals are stable under ambient left multiplication. -/
theorem productSpace_left (I J : AlgebraIdeal K A) (a b : A)
    (hb : b ∈ productSpace I J) : a * b ∈ productSpace I J := by
  have h : productSpace I J ≤ (productSpace I J).comap (LinearMap.mul K A a) := by
    apply Submodule.map₂_le.mpr
    intro x hx y hy
    change a * (x * y) ∈ productSpace I J
    rw [← mul_assoc]
    exact Submodule.apply_mem_map₂ _ (I.mul_mem_left a x hx) hy
  exact h hb

/-- Products of two ideals are stable under ambient right multiplication. -/
theorem productSpace_right (I J : AlgebraIdeal K A) (a b : A)
    (hb : b ∈ productSpace I J) : b * a ∈ productSpace I J := by
  have h : productSpace I J ≤ (productSpace I J).comap ((LinearMap.mul K A).flip a) := by
    apply Submodule.map₂_le.mpr
    intro x hx y hy
    change (x * y) * a ∈ productSpace I J
    rw [mul_assoc]
    exact Submodule.apply_mem_map₂ _ hx (J.mul_mem_right a y hy)
  exact h hb

/-- Ideal multiplication is the span of genuine products. -/
def product (I J : AlgebraIdeal K A) : AlgebraIdeal K A where
  subalgebra :=
    { carrier := productSpace I J
      zero_mem' := (productSpace I J).zero_mem
      add_mem' := (productSpace I J).add_mem
      smul_mem' := fun r _ hx => (productSpace I J).smul_mem r hx
      mul_mem' := fun _ hy => productSpace_left I J _ _ hy }
  mul_mem_left := productSpace_left I J
  mul_mem_right := productSpace_right I J

/-- Each generating product belongs to the product ideal. -/
theorem mul_mem_product (I J : AlgebraIdeal K A) (a b : A)
    (ha : a ∈ I.subalgebra) (hb : b ∈ J.subalgebra) :
    a * b ∈ (product I J).subalgebra := Submodule.apply_mem_map₂ _ ha hb

/-- A product ideal is contained in its left factor. -/
theorem product_le_left (I J : AlgebraIdeal K A) :
    (product I J).subalgebra.toSubmodule ≤ I.subalgebra.toSubmodule :=
  Submodule.map₂_le.mpr (fun a ha b _ => I.mul_mem_right b a ha)

/-- A product ideal is contained in its right factor. -/
theorem product_le_right (I J : AlgebraIdeal K A) :
    (product I J).subalgebra.toSubmodule ≤ J.subalgebra.toSubmodule :=
  Submodule.map₂_le.mpr (fun a _ b hb => J.mul_mem_left a b hb)

/-- Increasing either input ideal can only increase its product. -/
theorem product_mono {I I' J J' : AlgebraIdeal K A}
    (hI : I.subalgebra.toSubmodule ≤ I'.subalgebra.toSubmodule)
    (hJ : J.subalgebra.toSubmodule ≤ J'.subalgebra.toSubmodule) :
    (product I J).subalgebra.toSubmodule ≤ (product I' J').subalgebra.toSubmodule :=
  Submodule.map₂_le_map₂ hI hJ

/-- The positive ideal powers, indexed so that power 0 is the ideal itself. -/
def positivePower (I : AlgebraIdeal K A) : Nat → AlgebraIdeal K A
  | 0 => I
  | n + 1 => product I (positivePower I n)

/-- Every positive power is a subideal of its original ideal. -/
theorem positivePower_le (I : AlgebraIdeal K A) (n : Nat) :
    (positivePower I n).subalgebra.toSubmodule ≤ I.subalgebra.toSubmodule := by
  cases n with
  | zero => exact le_rfl
  | succ n => exact product_le_left I (positivePower I n)

/-- Positive powers respect inclusion of ideals. -/
theorem positivePower_mono {I J : AlgebraIdeal K A}
    (h : I.subalgebra.toSubmodule ≤ J.subalgebra.toSubmodule) (n : Nat) :
    (positivePower I n).subalgebra.toSubmodule ≤ (positivePower J n).subalgebra.toSubmodule := by
  induction n with
  | zero => exact h
  | succ n ih => exact product_mono h ih

/-- A nilpotent ideal has a zero positive power. -/
def IsNilpotentIdeal (I : AlgebraIdeal K A) : Prop :=
  ∃ n, (positivePower I n).subalgebra.toSubmodule = ⊥

/-- Subideals of nilpotent ideals are nilpotent. -/
theorem nilpotent_of_le {I J : AlgebraIdeal K A}
    (h : I.subalgebra.toSubmodule ≤ J.subalgebra.toSubmodule)
    (hJ : IsNilpotentIdeal J) : IsNilpotentIdeal I := by
  obtain ⟨n, hn⟩ := hJ
  refine ⟨n, le_bot_iff.mp ?_⟩
  exact (positivePower_mono h n).trans (le_of_eq hn)

/-- A nonzero nilpotent ideal strictly contains its square. -/
theorem square_lt_of_nilpotent (I : AlgebraIdeal K A) (hI : IsNilpotentIdeal I)
    (hne : I.subalgebra.toSubmodule ≠ ⊥) :
    (product I I).subalgebra.toSubmodule < I.subalgebra.toSubmodule := by
  apply lt_of_le_of_ne (product_le_left I I)
  intro heq
  have hp : ∀ n, (positivePower I n).subalgebra.toSubmodule = I.subalgebra.toSubmodule := by
    intro n
    induction n with
    | zero => rfl
    | succ n ih =>
      change Submodule.map₂ (LinearMap.mul K A) I.subalgebra.toSubmodule
        (positivePower I n).subalgebra.toSubmodule = I.subalgebra.toSubmodule
      rw [ih]
      exact heq
  obtain ⟨n, hn⟩ := hI
  exact hne ((hp n).symm.trans hn)

variable {B : Type u} [NonUnitalRing B] [Module K B]
  [SMulCommClass K B B] [IsScalarTower K B B]

/-- Homomorphisms carry positive ideal powers into the corresponding powers. -/
theorem positivePower_map_le (f : A →ₙₐ[K] B) (I : AlgebraIdeal K A)
    (J : AlgebraIdeal K B) (h : ∀ a ∈ I.subalgebra, f a ∈ J.subalgebra) (n : Nat) :
    (positivePower I n).subalgebra.toSubmodule ≤
      (positivePower J n).subalgebra.toSubmodule.comap (LinearMap.ofClass f) := by
  induction n with
  | zero => exact h
  | succ n ih =>
    apply Submodule.map₂_le.mpr
    intro a ha b hb
    change f (a * b) ∈ (product J (positivePower J n)).subalgebra
    rw [map_mul]
    exact mul_mem_product J (positivePower J n) (f a) (f b) (h a ha) (ih hb)

/-- An injectively embedded ideal of a nilpotent ideal is nilpotent. -/
theorem nilpotent_of_injective_map (f : A →ₙₐ[K] B) (hf : Function.Injective f)
    (I : AlgebraIdeal K A) (J : AlgebraIdeal K B)
    (h : ∀ a ∈ I.subalgebra, f a ∈ J.subalgebra) (hJ : IsNilpotentIdeal J) :
    IsNilpotentIdeal I := by
  obtain ⟨n, hn⟩ := hJ
  refine ⟨n, le_bot_iff.mp ?_⟩
  intro a ha
  have hm := positivePower_map_le f I J h n ha
  change f a ∈ (positivePower J n).subalgebra.toSubmodule at hm
  rw [hn] at hm
  exact hf (hm.trans (map_zero f).symm)

/-- The genuine two-sided kernel ideal of a nonunital algebra homomorphism. -/
def kernel (f : A →ₙₐ[K] B) : AlgebraIdeal K A where
  subalgebra :=
    { carrier := {a | f a = 0}
      zero_mem' := map_zero f
      add_mem' := by intro a b ha hb; simp_all
      mul_mem' := by intro a b ha hb; simp_all
      smul_mem' := by intro r a ha; simp_all }
  mul_mem_left := by
    intro a b hb
    change f b = 0 at hb
    change f (a * b) = 0
    simp [hb]
  mul_mem_right := by
    intro a b hb
    change f b = 0 at hb
    change f (b * a) = 0
    simp [hb]

end Hochschild1945.AlgebraIdeal
namespace Hochschild1945.AlgebraIdeal
universe u
open scoped Pointwise
variable {K A : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A]

/-- The ideal's actual embedded vector subspace in the unitization. -/
def inrSpace (I : AlgebraIdeal K A) : Submodule K (Unitization K A) :=
  I.subalgebra.toSubmodule.map (Unitization.inrHom K K A)

/-- Images of positive ideal powers lie in the corresponding unitization powers. -/
theorem positivePower_inr_le (I : AlgebraIdeal K A) (n : Nat) :
    (positivePower I n).subalgebra.toSubmodule.map (Unitization.inrHom K K A) ≤
      (inrSpace I) ^ (n + 1) := by
  induction n with
  | zero => simp [positivePower, inrSpace]
  | succ n ih =>
    rw [pow_succ']
    apply Submodule.map_le_iff_le_comap.mpr
    apply Submodule.map₂_le.mpr
    intro a ha b hb
    change (Unitization.inr (a * b) : Unitization K A) ∈
      inrSpace I * (inrSpace I) ^ (n + 1)
    rw [Unitization.inr_mul]
    apply Submodule.mul_mem_mul
    · exact ⟨a, ha, rfl⟩
    · exact ih ⟨b, hb, rfl⟩

/-- The classical radical nilpotence statement gives the corresponding
zero vector-space power for every actual ideal contained in the radical. -/
theorem nilpotent_of_mem_radical [FiniteDimensional K A] (I : AlgebraIdeal K A)
    (hI : ∀ a ∈ I.subalgebra, Unitization.inr a ∈ Ring.jacobson (Unitization K A)) :
    IsNilpotentIdeal I := by
  classical
  obtain ⟨n, hn, hnil⟩ := cited_radical_nilpotent K A
  have hp : (inrSpace I) ^ n = ⊥ := by
    rw [Submodule.pow_eq_span_pow_set]
    apply le_bot_iff.mp
    apply Submodule.span_le.mpr
    intro x hx
    obtain ⟨f, hf⟩ := Set.mem_pow.mp hx
    have hex : ∀ i, ∃ a : A, a ∈ I.subalgebra ∧ Unitization.inr a = (f i : Unitization K A) := by
      intro i
      exact (f i).property
    choose a ha he using hex
    have hz := hnil a (fun i => hI (a i) (ha i))
    have hfn : (fun i => Unitization.inr (a i)) = (fun i => (f i : Unitization K A)) := funext he
    rw [hfn, hf] at hz
    exact hz
  obtain ⟨m, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (Nat.ne_of_gt hn)
  refine ⟨m, le_bot_iff.mp ?_⟩
  intro a ha
  have hmem := positivePower_inr_le I m ⟨a, ha, rfl⟩
  rw [hp] at hmem
  have hz : (Unitization.inr a : Unitization K A) = 0 := hmem
  apply (Unitization.inr_injective (R := K))
  simpa using hz

end Hochschild1945.AlgebraIdeal
namespace Hochschild1945.Extension
universe u
open AlgebraIdeal
variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

attribute [local instance] AlgebraIdeal.quotientMul AlgebraIdeal.quotientRing
  AlgebraIdeal.quotientSMulComm AlgebraIdeal.quotientScalarTower

/-- The actual two-sided ideal underlying the extension kernel. -/
def kernelAlgebraIdeal (E : Extension K A B) : AlgebraIdeal K B := AlgebraIdeal.kernel E.sigma

/-- Quotienting an extension by an ideal contained in its kernel. -/
def quotientByIdeal (E : Extension K A B) (I : AlgebraIdeal K B)
    (hI : I.subalgebra.toSubmodule ≤ E.kernel) : Extension K A I.Quotient where
  sigma := I.quotientLift E.sigma (fun _ ha => hI ha)
  surjective := I.quotientLift_surjective E.sigma _ E.surjective

/-- The quotient extension still sends a representative to its original image. -/
@[simp] theorem quotientByIdeal_sigma_mk (E : Extension K A B) (I : AlgebraIdeal K B)
    (hI : I.subalgebra.toSubmodule ≤ E.kernel) (b : B) :
    (quotientByIdeal E I hI).sigma (I.quotientMap b) = E.sigma b := rfl

/-- The square of the actual kernel ideal. -/
def kernelSquare (E : Extension K A B) : AlgebraIdeal K B :=
  product E.kernelAlgebraIdeal E.kernelAlgebraIdeal

/-- Every kernel-square element is still in the kernel. -/
theorem kernelSquare_le (E : Extension K A B) :
    E.kernelSquare.subalgebra.toSubmodule ≤ E.kernel :=
  product_le_left _ _

/-- The extension obtained by quotienting by the square of its kernel. -/
def squareQuotient (E : Extension K A B) : Extension K A E.kernelSquare.Quotient :=
  quotientByIdeal E E.kernelSquare E.kernelSquare_le

/-- The quotient by the kernel square is a genuine singular extension. -/
theorem squareQuotient_singular (E : Extension K A B) : E.squareQuotient.IsSingular := by
  intro x y hx hy
  obtain ⟨b, rfl⟩ := E.kernelSquare.quotientMap_surjective x
  obtain ⟨c, rfl⟩ := E.kernelSquare.quotientMap_surjective y
  rw [← map_mul, AlgebraIdeal.quotientMap_eq_zero]
  exact mul_mem_product _ _ b c hx hy

/-- A zero-kernel extension already has an algebra section. -/
theorem hasSection_of_kernel_eq_bot (E : Extension K A B) (hE : E.kernel = ⊥) :
    E.HasSection := by
  classical
  let e : B ≃ₗ[K] A := LinearEquiv.ofBijective E.linear
    ⟨LinearMap.ker_eq_bot.mp hE, E.surjective⟩
  let s : A →ₙₐ[K] B :=
    { toFun := e.symm
      map_zero' := map_zero e.symm
      map_add' := map_add e.symm
      map_smul' := map_smul e.symm
      map_mul' := by
        intro a b
        apply e.injective
        change e (e.symm (a * b)) = E.sigma (e.symm a * e.symm b)
        rw [e.apply_symm_apply, map_mul]
        exact congrArg₂ (· * ·) (e.apply_symm_apply a).symm (e.apply_symm_apply b).symm }
  exact ⟨s, e.apply_symm_apply⟩

/-- Pull a section's image in the singular quotient back to a genuine subalgebra. -/
def sectionPreimage (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient) : NonUnitalSubalgebra K B :=
  s.range.comap E.kernelSquare.quotientMap

/-- The pulled-back subalgebra is an extension of A under the original map. -/
noncomputable def sectionPreimageExtension (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a) :
    Extension K A (E.sectionPreimage s) where
  sigma := E.sigma.comp (NonUnitalSubalgebraClass.subtype (E.sectionPreimage s))
  surjective := by
    intro a
    obtain ⟨b, hb⟩ := E.kernelSquare.quotientMap_surjective (s a)
    refine ⟨⟨b, ?_⟩, ?_⟩
    · exact ⟨a, hb.symm⟩
    · change E.sigma b = a
      calc
        E.sigma b = E.squareQuotient.sigma (E.kernelSquare.quotientMap b) := rfl
        _ = E.squareQuotient.sigma (s a) := congrArg E.squareQuotient.sigma hb
        _ = a := hs a

/-- The new extension kernel consists of elements of the old kernel square. -/
theorem sectionPreimage_kernel_mem (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a)
    (b : E.sectionPreimage s)
    (hb : (E.sectionPreimageExtension s hs).sigma b = 0) :
    (b : B) ∈ E.kernelSquare.subalgebra := by
  obtain ⟨a, ha⟩ := b.property
  have hz : a = 0 := by
    calc
      a = E.squareQuotient.sigma (s a) := (hs a).symm
      _ = E.squareQuotient.sigma (E.kernelSquare.quotientMap b) := congrArg _ ha
      _ = 0 := hb
  apply (AlgebraIdeal.quotientMap_eq_zero _ _).mp
  erw [← ha, hz, map_zero]

/-- An algebra section of the pulled-back extension is one of the original extension. -/
theorem hasSection_of_preimageSection (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a)
    (h : (E.sectionPreimageExtension s hs).HasSection) : E.HasSection := by
  obtain ⟨t, ht⟩ := h
  exact ⟨(NonUnitalSubalgebraClass.subtype (E.sectionPreimage s)).comp t, ht⟩

/-- The new kernel embeds linearly into the original kernel square. -/
def sectionPreimageKernelEmbedding (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a) :
    (E.sectionPreimageExtension s hs).kernel →ₗ[K] E.kernelSquare.subalgebra.toSubmodule where
  toFun b := ⟨b.val.val, E.sectionPreimage_kernel_mem s hs b.val b.property⟩
  map_add' := by intros; rfl
  map_smul' := by intros; rfl

/-- The kernel embedding forgets only subtype proofs. -/
theorem sectionPreimageKernelEmbedding_injective (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a) :
    Function.Injective (E.sectionPreimageKernelEmbedding s hs) := by
  intro x y h
  apply Subtype.ext
  apply Subtype.ext
  exact congrArg (fun z : E.kernelSquare.subalgebra.toSubmodule => (z : B)) h

/-- Nilpotence passes from the original kernel to the pulled-back kernel. -/
theorem sectionPreimage_kernel_nilpotent (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a)
    (hE : IsNilpotentIdeal E.kernelAlgebraIdeal) :
    IsNilpotentIdeal (E.sectionPreimageExtension s hs).kernelAlgebraIdeal := by
  apply nilpotent_of_injective_map
    (NonUnitalSubalgebraClass.subtype (E.sectionPreimage s)) Subtype.coe_injective
    (E.sectionPreimageExtension s hs).kernelAlgebraIdeal E.kernelSquare
  · intro b hb
    exact E.sectionPreimage_kernel_mem s hs b hb
  · exact nilpotent_of_le (product_le_left _ _) hE

/-- The pulled-back kernel has smaller dimension when the nilpotent kernel is nonzero. -/
theorem sectionPreimage_kernel_finrank_lt [FiniteDimensional K B] (E : Extension K A B)
    (s : A →ₙₐ[K] E.kernelSquare.Quotient)
    (hs : ∀ a, E.squareQuotient.sigma (s a) = a)
    (hE : IsNilpotentIdeal E.kernelAlgebraIdeal) (hne : E.kernel ≠ ⊥) :
    Module.finrank K (E.sectionPreimageExtension s hs).kernel < Module.finrank K E.kernel := by
  have hsq : E.kernelSquare.subalgebra.toSubmodule < E.kernel :=
    square_lt_of_nilpotent E.kernelAlgebraIdeal hE hne
  exact lt_of_le_of_lt
    (LinearMap.finrank_le_finrank_of_injective (E.sectionPreimageKernelEmbedding_injective s hs))
    (Submodule.finrank_lt_finrank_of_lt hsq)

end Hochschild1945.Extension
namespace Hochschild1945.Extension
universe u
open AlgebraIdeal
variable {K A : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]

attribute [local instance] AlgebraIdeal.quotientMul AlgebraIdeal.quotientRing
  AlgebraIdeal.quotientSMulComm AlgebraIdeal.quotientScalarTower

/-- The source's induction on the finite dimension of a nilpotent kernel.
The quotient by the kernel square splits by the singular hypothesis; its
section pulls back to an extension with a strictly smaller nilpotent kernel. -/
theorem nilpotent_sections_by_dimension
    (h : ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
      [IsScalarTower K B B] [FiniteDimensional K B],
      ∀ E : Extension K A B, E.IsSingular → E.HasSection) :
    ∀ n : Nat, ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
      [IsScalarTower K B B] [FiniteDimensional K B],
      ∀ E : Extension K A B, Module.finrank K E.kernel = n →
        IsNilpotentIdeal E.kernelAlgebraIdeal → E.HasSection := by
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
    intro B _ _ _ _ _ E hdim hnil
    by_cases hz : E.kernel = ⊥
    · exact E.hasSection_of_kernel_eq_bot hz
    · obtain ⟨s, hs⟩ := h E.kernelSquare.Quotient E.squareQuotient E.squareQuotient_singular
      let : FiniteDimensional K (E.sectionPreimage s) :=
        FiniteDimensional.of_injective
          (LinearMap.ofClass (NonUnitalSubalgebraClass.subtype (E.sectionPreimage s)))
          Subtype.coe_injective
      have hlt : Module.finrank K (E.sectionPreimageExtension s hs).kernel < n := by
        rw [← hdim]
        exact E.sectionPreimage_kernel_finrank_lt s hs hnil hz
      have hsmall := ih _ hlt (E.sectionPreimage s) (E.sectionPreimageExtension s hs) rfl
        (E.sectionPreimage_kernel_nilpotent s hs hnil)
      exact E.hasSection_of_preimageSection s hs hsmall

/-- Any finite extension with nilpotent kernel splits if every singular one splits. -/
theorem hasSection_of_nilpotent
    (h : ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
      [IsScalarTower K B B] [FiniteDimensional K B],
      ∀ E : Extension K A B, E.IsSingular → E.HasSection)
    {B : Type u} [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
    [IsScalarTower K B B] [FiniteDimensional K B]
    (E : Extension K A B) (hnil : IsNilpotentIdeal E.kernelAlgebraIdeal) : E.HasSection :=
  nilpotent_sections_by_dimension h (Module.finrank K E.kernel) B E rfl hnil

end Hochschild1945.Extension
namespace Hochschild1945.Extension
universe u
open AlgebraIdeal
variable {K A : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]

attribute [local instance] idealFiniteDimensional

/-- Reduce a finite extension to one with nilpotent kernel using its actual
radical quotient. Complement the image of the original kernel in that quotient
and pull the complement back. This skips the source's intermediate quotient by
the intersection of the kernel and radical, while proving the same reduction. -/
theorem hasSection_of_nilpotent_reduction
    (h : ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
      [IsScalarTower K B B] [FiniteDimensional K B],
      ∀ E : Extension K A B, IsNilpotentIdeal E.kernelAlgebraIdeal → E.HasSection)
    {B : Type u} [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
    [IsScalarTower K B B] [FiniteDimensional K B] (E : Extension K A B) : E.HasSection := by
  obtain ⟨Q⟩ := cited_radical_quotient K B
  let := Q.ring
  let := Q.module
  let := Q.comm
  let := Q.tower
  let := Q.finite
  let imageKernel := E.kernelAlgebraIdeal.mapSurjective Q.quotient Q.surjective
  have hsemi : Semisimple K imageKernel.subalgebra :=
    (cited_semisimple_ideal_structure K Q.carrier Q.semisimple imageKernel).1
  obtain ⟨J, hJ⟩ := semisimple_ideal_summand imageKernel hsemi
  let D := J.comap Q.quotient
  let ED : Extension K A D.subalgebra :=
    { sigma := E.sigma.comp (NonUnitalSubalgebraClass.subtype D.subalgebra)
      surjective := by
        intro a
        obtain ⟨b, hb⟩ := E.surjective a
        obtain ⟨x, y, hx, hy, hxy⟩ :=
          Submodule.codisjoint_iff_exists_add_eq.mp hJ.codisjoint (Q.quotient b)
        obtain ⟨k, hk, hqk⟩ := NonUnitalSubalgebra.mem_map.mp hx
        refine ⟨⟨b - k, ?_⟩, ?_⟩
        · change Q.quotient (b - k) ∈ J.subalgebra
          rw [map_sub, hqk, ← hxy]
          simpa using hy
        · change E.sigma (b - k) = a
          rw [map_sub, (hk : E.sigma k = 0), sub_zero]
          exact hb }
  let R := AlgebraIdeal.kernel Q.quotient
  have hR : IsNilpotentIdeal R := nilpotent_of_mem_radical R (by
    intro b hb
    exact (Q.kernel b).mp hb)
  have hnil : IsNilpotentIdeal ED.kernelAlgebraIdeal := by
    apply nilpotent_of_injective_map
      (NonUnitalSubalgebraClass.subtype D.subalgebra) Subtype.coe_injective
      ED.kernelAlgebraIdeal R _ hR
    intro b hb
    change Q.quotient b = 0
    apply Submodule.disjoint_def.mp hJ.disjoint (Q.quotient b)
    · exact NonUnitalSubalgebra.mem_map.mpr ⟨(b : B), hb, rfl⟩
    · exact b.property
  obtain ⟨s, hs⟩ := h D.subalgebra ED hnil
  exact ⟨(NonUnitalSubalgebraClass.subtype D.subalgebra).comp s, hs⟩

end Hochschild1945.Extension
namespace Hochschild1945
universe u
variable (K A : Type u) [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]

/-- **Proposition 6.1** (Hochschild). A finite algebra segregated in every
singular finite extension is segregated in every finite extension. The radical
reduction uses the proved image-complement variant recorded in the header;
the nilpotent-kernel step follows the source induction on kernel dimension.
The local proof is complete relative to the explicit cited radical and
semisimple-ideal facts. -/
theorem segregatedInEveryExtension_of_singular
    (h : SegregatedInEverySingularExtension K A) : SegregatedInEveryExtension K A := by
  have hs : ∀ (B : Type u) [NonUnitalRing B] [Module K B] [SMulCommClass K B B]
      [IsScalarTower K B B] [FiniteDimensional K B],
      ∀ E : Extension K A B, E.IsSingular → E.HasSection := by
    intro B _ _ _ _ _ E hE
    exact E.isSegregated_iff_hasSection.mp (h B E hE)
  intro B _ _ _ _ _ E
  apply E.isSegregated_iff_hasSection.mpr
  apply Extension.hasSection_of_nilpotent_reduction _ E
  intro C _ _ _ _ _ F hF
  exact Extension.hasSection_of_nilpotent hs F hF

end Hochschild1945
