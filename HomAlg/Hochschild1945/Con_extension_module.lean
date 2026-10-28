import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_isomorphic_extensions
import HomAlg.Hochschild1945.Def_two_sided_module

/-!
```yaml node
id: "Hochschild1945.Con_extension_module"
doc: "Hochschild1945"
kind: "construction"
source:
  label: "Construction (unnumbered, p. 65)"
  pages:
    - 65
    - 66
  chapter: "6"
tags:
  - "module"
  - "singular-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_extension"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Def_isomorphic_extensions"
  proof: []
decls:
  - "Hochschild1945.Extension.kernelModule"
  - "Hochschild1945.Extension.kernelModule_independent"
  - "Hochschild1945.Extension.kernelModule_operator_isomorphic"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension.kernelModule:
        statement_sha256: "771ce165145d6953c96d536e73f9497b8182b5de665cb84375397ebf12553e6c"
        type_hash: "0000000010ce1c6c"
        meaning_hash: "3ac9161c4bc7b525"
      Hochschild1945.Extension.kernelModule_independent:
        statement_sha256: "73b706628d774fcdd4a18c13290106f4c6093565d050b89512a5f6c4100bdc07"
        type_hash: "00000000c2c942d9"
        meaning_hash: "0813747b901d0cb6"
      Hochschild1945.Extension.kernelModule_operator_isomorphic:
        statement_sha256: "183ecf60bc569186c3974254e46a1fb3e552b083381b10ab99390bfed8468200"
        type_hash: "0000000058c52529"
        meaning_hash: "c453979aabcb773d"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Module associated with a singular extension"
```

## Statement

Let $\{\mathfrak{B},\sigma\}$ be a singular extension of $\mathfrak{A}$ with kernel $\mathfrak{K}$. Let $\rho$ be any linear mapping of $\mathfrak{A}$ into $\mathfrak{B}$ such that
\[
\sigma\{\rho\{a\}\}=a,\quad\hbox{for every } a\in\mathfrak{A},\quad\hbox{or---which is equivalent---}
\]
\begin{equation}\tag{1}
\rho\{\sigma\{b\}\}\equiv b\bmod\mathfrak{K},\quad\hbox{for every }b\in\mathfrak{B}.
\end{equation}

We can make $\mathfrak{K}$ a two-sided $\mathfrak{A}$-module by the definitions $a\cdot k=\rho\{a\}k$, $k\cdot a=k\rho\{a\}$, where $k\in\mathfrak{K}$, $a\in\mathfrak{A}$.

## Proof

Since the difference of any two mappings $\rho$ satisfying (1) is a mapping of $\mathfrak{A}$ into $\mathfrak{K}$ and since $\mathfrak{K}^2=\{0\}$ it is clear that $k\cdot a$ and $a\cdot k$ are independent of the particular mapping $\rho$ we have selected. Thus the two-sided $\mathfrak{A}$-module $\mathfrak{K}$ is uniquely determined by the extension $\{\mathfrak{B},\sigma\}$. Furthermore, if $\{\mathfrak{B}^*,\sigma^*\}$ is an isomorphic extension, we have:
\[
\sigma^*\{\rho^*\{a\}\}=a=\sigma\{\rho\{a\}\}=\sigma^*I\{\rho\{a\}\},\quad\hbox{i.e. }\rho^*\{a\}\equiv I\{\rho\{a\}\}\bmod\mathfrak{K}^*.
\]
Hence,
\[
a\cdot I\{k\}=\rho^*\{a\}I\{k\}=I\{\rho\{a\}\}I\{k\}=I\{a\cdot k\},
\]

and, similarly,
\[
I\{k\}\cdot a=I\{k\cdot a\}.
\]
This means that $I$ is an operator isomorphism between the two-sided $\mathfrak{A}$-modules $\mathfrak{K}$ and $\mathfrak{K}^*$, and we have shown that isomorphic extensions lead to operator-isomorphic $\mathfrak{A}$-modules.

## Description

Constructs the kernel bimodule of a singular extension and shows that it is independent of the chosen linear section.
-/

namespace Hochschild1945
namespace Extension

universe u

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

/-- The left action defined by lifting an algebra element and multiplying it
with a kernel element, exactly as in the source. -/
def kernelLeft (E : Extension K A B) (ρ : A →ₗ[K] B) :
    A →ₗ[K] E.kernel →ₗ[K] E.kernel :=
  LinearMap.mk₂ K (fun a k => ⟨ρ a * k, by
    change E.sigma (ρ a * k) = 0
    have hk : E.sigma k = 0 := k.property
    simp [map_mul, hk]⟩)
    (by intros; apply Subtype.ext; simp [add_mul])
    (by intros; apply Subtype.ext; simp [smul_mul_assoc])
    (by intros; apply Subtype.ext; simp [mul_add])
    (by intros; apply Subtype.ext; simp [mul_smul_comm])

/-- The source's right action is multiplication by a lifted algebra element. -/
def kernelRight (E : Extension K A B) (ρ : A →ₗ[K] B) :
    E.kernel →ₗ[K] A →ₗ[K] E.kernel :=
  LinearMap.mk₂ K (fun k a => ⟨k * ρ a, by
    change E.sigma (k * ρ a) = 0
    have hk : E.sigma k = 0 := k.property
    simp [map_mul, hk]⟩)
    (by intros; apply Subtype.ext; simp [add_mul])
    (by intros; apply Subtype.ext; simp [smul_mul_assoc])
    (by intros; apply Subtype.ext; simp [mul_add])
    (by intros; apply Subtype.ext; simp [mul_smul_comm])

/-- **Construction (unnumbered, p. 65)** (Hochschild). A linear section makes
the kernel of a singular extension into a two-sided module. Associativity uses
the fact that the defect of the section lies in the square-zero kernel. -/
def kernelModule (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    TwoSidedModule K A E.kernel where
  left := kernelLeft E ρ
  right := kernelRight E ρ
  left_assoc := by
    intro a b k
    apply Subtype.ext
    change ρ (a * b) * k = ρ a * (ρ b * k)
    have hd : E.sigma (ρ (a * b) - ρ a * ρ b) = 0 := by simp [map_sub, map_mul, hρ]
    have hz := hE (ρ (a * b) - ρ a * ρ b) k hd k.property
    rw [sub_mul, mul_assoc] at hz
    exact sub_eq_zero.mp hz
  right_assoc := by
    intro k a b
    apply Subtype.ext
    change (k * ρ a) * ρ b = k * ρ (a * b)
    have hd : E.sigma (ρ a * ρ b - ρ (a * b)) = 0 := by simp [map_sub, map_mul, hρ]
    have hz := hE k (ρ a * ρ b - ρ (a * b)) k.property hd
    rw [mul_sub, ← mul_assoc] at hz
    exact sub_eq_zero.mp hz
  left_right := by
    intro a k b
    apply Subtype.ext
    exact mul_assoc (ρ a) k (ρ b)

/-- The source's left action does not depend on which linear section was selected. -/
theorem kernelLeft_independent (E : Extension K A B) (hE : E.IsSingular)
    (ρ τ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (hτ : ∀ a, E.sigma (τ a) = a) : kernelLeft E ρ = kernelLeft E τ := by
  ext a k
  change ρ a * k = τ a * k
  have hd : E.sigma (ρ a - τ a) = 0 := by simp [map_sub, hρ, hτ]
  have hz := hE (ρ a - τ a) k hd k.property
  rw [sub_mul] at hz
  exact sub_eq_zero.mp hz

/-- The source's right action is likewise independent of the section. -/
theorem kernelRight_independent (E : Extension K A B) (hE : E.IsSingular)
    (ρ τ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (hτ : ∀ a, E.sigma (τ a) = a) : kernelRight E ρ = kernelRight E τ := by
  ext k a
  change k * ρ a = k * τ a
  have hd : E.sigma (ρ a - τ a) = 0 := by simp [map_sub, hρ, hτ]
  have hz := hE k (ρ a - τ a) k.property hd
  rw [mul_sub] at hz
  exact sub_eq_zero.mp hz

/-- **Construction (unnumbered, p. 65) (independence)** (Hochschild).
The complete two-sided module structure is independent of the linear section. -/
theorem kernelModule_independent (E : Extension K A B) (hE : E.IsSingular)
    (ρ τ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (hτ : ∀ a, E.sigma (τ a) = a) : kernelModule E hE ρ hρ = kernelModule E hE τ hτ := by
  have hl := kernelLeft_independent E hE ρ τ hρ hτ
  have hr := kernelRight_independent E hE ρ τ hρ hτ
  unfold kernelModule
  congr

variable {C : Type u} [NonUnitalRing C] [Module K C]
  [SMulCommClass K C C] [IsScalarTower K C C]

/-- An extension isomorphism restricts to a linear equivalence of the kernels. -/
def Isomorphism.kernelEquiv {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) : E.kernel ≃ₗ[K] F.kernel where
  toFun := fun k => ⟨I.toLinearEquiv k, by
    change F.sigma (I.toLinearEquiv k) = 0
    rw [I.commutes]
    exact k.property⟩
  invFun := fun k => ⟨I.toLinearEquiv.symm k, by
    change E.sigma (I.symm.toLinearEquiv k) = 0
    rw [I.symm.commutes]
    exact k.property⟩
  left_inv := by
    intro k
    apply Subtype.ext
    exact I.toLinearEquiv.symm_apply_apply k
  right_inv := by
    intro k
    apply Subtype.ext
    exact I.toLinearEquiv.apply_symm_apply k
  map_add' := by intros; apply Subtype.ext; simp
  map_smul' := by intros; apply Subtype.ext; simp

/-- Singularity is preserved by an isomorphism of extensions. -/
theorem Isomorphism.singular {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) (hE : E.IsSingular) : F.IsSingular := by
  intro x y hx hy
  have hx' : E.sigma (I.toLinearEquiv.symm x) = 0 := by
    change E.sigma (I.symm.toLinearEquiv x) = 0
    rw [I.symm.commutes]
    exact hx
  have hy' : E.sigma (I.toLinearEquiv.symm y) = 0 := by
    change E.sigma (I.symm.toLinearEquiv y) = 0
    rw [I.symm.commutes]
    exact hy
  calc
    x * y = I.toLinearEquiv (I.toLinearEquiv.symm x * I.toLinearEquiv.symm y) := by
      rw [I.map_mul']
      simp
    _ = 0 := by rw [hE _ _ hx' hy', map_zero]

/-- The kernel equivalence intertwines the left actions from arbitrary sections. -/
theorem Isomorphism.kernelEquiv_left {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (τ : A →ₗ[K] C)
    (hρ : ∀ a, E.sigma (ρ a) = a) (hτ : ∀ a, F.sigma (τ a) = a)
    (a : A) (k : E.kernel) :
    I.kernelEquiv ((E.kernelModule hE ρ hρ).left a k) =
      (F.kernelModule (I.singular hE) τ hτ).left a (I.kernelEquiv k) := by
  apply Subtype.ext
  change I.toLinearEquiv (ρ a * k) = τ a * I.toLinearEquiv k
  rw [I.map_mul']
  have hd : F.sigma (I.toLinearEquiv (ρ a) - τ a) = 0 := by
    rw [map_sub, I.commutes, hρ, hτ, sub_self]
  have hk : F.sigma (I.toLinearEquiv k) = 0 := by
    rw [I.commutes]
    exact k.property
  have hz := I.singular hE (I.toLinearEquiv (ρ a) - τ a) (I.toLinearEquiv k) hd hk
  rw [sub_mul] at hz
  exact sub_eq_zero.mp hz

/-- The kernel equivalence also intertwines the right actions. -/
theorem Isomorphism.kernelEquiv_right {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (τ : A →ₗ[K] C)
    (hρ : ∀ a, E.sigma (ρ a) = a) (hτ : ∀ a, F.sigma (τ a) = a)
    (k : E.kernel) (a : A) :
    I.kernelEquiv ((E.kernelModule hE ρ hρ).right k a) =
      (F.kernelModule (I.singular hE) τ hτ).right (I.kernelEquiv k) a := by
  apply Subtype.ext
  change I.toLinearEquiv (k * ρ a) = I.toLinearEquiv k * τ a
  rw [I.map_mul']
  have hd : F.sigma (I.toLinearEquiv (ρ a) - τ a) = 0 := by
    rw [map_sub, I.commutes, hρ, hτ, sub_self]
  have hk : F.sigma (I.toLinearEquiv k) = 0 := by
    rw [I.commutes]
    exact k.property
  have hz := I.singular hE (I.toLinearEquiv k) (I.toLinearEquiv (ρ a) - τ a) hk hd
  rw [mul_sub] at hz
  exact sub_eq_zero.mp hz

/-- **Construction (unnumbered, p. 65) (isomorphic extensions)** (Hochschild).
Isomorphic singular extensions give operator-isomorphic two-sided modules,
independently of the linear sections used to describe their actions. -/
theorem kernelModule_operator_isomorphic {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (τ : A →ₗ[K] C)
    (hρ : ∀ a, E.sigma (ρ a) = a) (hτ : ∀ a, F.sigma (τ a) = a) :
    ∃ e : E.kernel ≃ₗ[K] F.kernel,
      (∀ a k, e ((E.kernelModule hE ρ hρ).left a k) =
        (F.kernelModule (I.singular hE) τ hτ).left a (e k)) ∧
      (∀ k a, e ((E.kernelModule hE ρ hρ).right k a) =
        (F.kernelModule (I.singular hE) τ hτ).right (e k) a) :=
  ⟨I.kernelEquiv, I.kernelEquiv_left hE ρ τ hρ hτ, I.kernelEquiv_right hE ρ τ hρ hτ⟩

end Extension
end Hochschild1945
