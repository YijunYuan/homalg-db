import HomAlg.Hochschild1945.Prop_1_1
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_bar_map
import Mathlib.Tactic.Abel

import HomAlg.Hochschild1945.Con_extension_module
import HomAlg.Hochschild1945.Def_2_2

/-!
```yaml node
id: "Hochschild1945.Con_extension_cocycle"
doc: "Hochschild1945"
kind: "construction"
source:
  label: "Construction (unnumbered, p. 66, 1)"
  pages:
    - 66
  chapter: "6"
tags:
  - "hochschild-cohomology"
  - "singular-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Con_extension_module"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_extension"
  proof:
    - "Hochschild1945.Con_bar_map"
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Prop_1_1"
decls:
  - "Hochschild1945.Extension.sectionCocycle"
  - "Hochschild1945.Extension.sectionCocycle_isCocycle"
  - "Hochschild1945.Extension.sectionCocycle_cohomologous"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension.sectionCocycle:
        statement_sha256: "aade04a9c935704edbd35732143a8f49b1c36a1d437b3068e2ca388302f72d2b"
        type_hash: "0000000021405e99"
        meaning_hash: "060769cd9881e848"
      Hochschild1945.Extension.sectionCocycle_isCocycle:
        statement_sha256: "4a8ad3e73e201b307a9ecaa8cedfa8c5dce98aa9645c402d337d7a6448293e26"
        type_hash: "00000000ab6c53a2"
        meaning_hash: "496d2d351541fa49"
      Hochschild1945.Extension.sectionCocycle_cohomologous:
        statement_sha256: "30b9e72a47197b618bea3ffd8373644f977756bcefbe8d6a23d5ca62fc04a8df"
        type_hash: "000000009863656f"
        meaning_hash: "7af1fd430cecdb1f"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Cocycle associated with a singular extension"
```

## Statement

Consider now the mapping $a_1\times a_2\to f_\rho\{a_1,a_2\}=\rho\{a_1\}\rho\{a_2\}-\rho\{a_1a_2\}$ of $\mathfrak{A}\times\mathfrak{A}$ into $\mathfrak{K}$. It is easy to verify that $f_\rho$ is a $(2,\mathfrak{K})$-cocycle of $\mathfrak{A}$.

## Proof

If $\rho'$ is a second linear mapping of $\mathfrak{A}$ into $\mathfrak{B}$ satisfying (1), we have:
\[
\begin{aligned}
f_\rho\{a_1,a_2\}-f_{\rho'}\{a_1,a_2\}
&=\rho\{a_1\}[\rho\{a_2\}-\rho'\{a_2\}]\\
&\quad-[\rho\{a_1a_2\}-\rho'\{a_1a_2\}]+[\rho\{a_1\}-\rho'\{a_1\}]\rho'\{a_2\}\\
&=a_1\cdot[\rho\{a_2\}-\rho'\{a_2\}]-[\rho\{a_1a_2\}-\rho'\{a_1a_2\}]\\
&\quad+[\rho\{a_1\}-\rho'\{a_1\}]\cdot a_2,
\end{aligned}
\]
i.e. $f_\rho-f_{\rho'}=\delta(\rho-\rho')$. Hence the cohomology class $\bar f$ of $f_\rho$ is uniquely determined by the extension $\{\mathfrak{B},\sigma\}$.

Now let $\{\mathfrak{B}^*,\sigma^*\}$ be a singular extension of $\mathfrak{A}$ which is isomorphic (by the isomorphism $I$) with $\{\mathfrak{B},\sigma\}$. Then $I\rho$ is clearly a linear mapping of $\mathfrak{A}$ into $\mathfrak{B}^*$ which satisfies (1). Hence $f_{I\rho}$ is a $(2,\mathfrak{K}^*)$-cocycle of $\mathfrak{A}$ which lies in the cohomology class determined by the extension $\{\mathfrak{B}^*,\sigma^*\}$. Since $f_{I\rho}=If_\rho$, the cohomology class determined by the extension $\{\mathfrak{B}^*,\sigma^*\}$ is the isomorphic image by $I$ of the cohomology class determined by $\{\mathfrak{B},\sigma\}$.

[uses `Hochschild1945.Con_bar_map`] [uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Def_two_sided_module`] [uses `Hochschild1945.Prop_1_1`]

## Description

Associates a two-cocycle to a linear section and proves that the resulting cohomology class depends only on the extension.

## Formalization notes


The `mathlib-bypass-proof` warning matches NonUnitalAlgHom because the extension
projection σ is an actual nonunital algebra homomorphism. This type is also
listed as a correspondence target of the source two-sided-module definition;
its occurrence here does not replace that definition or invoke a counterpart
cohomology theorem. The proof uses the source kernelModule, constructs
ρ(a)ρ(b)−ρ(ab) by TensorProduct.lift, and expands the source coboundary to prove
both cocyclehood and section independence by associativity. The exact source
proof dependencies remain present and verified.

-/

namespace Hochschild1945

open scoped TensorProduct

universe u

/-- The degree-two instance of the source coboundary on three pure tensor factors. -/
theorem delta_two_apply {K A P : Type u} [Field K] [NonUnitalRing A]
    [Module K A] [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
    [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)
    (f : Cochain K A P 2) (a b c : A) :
    delta M 2 f ((a ⊗ₜ[K] b) ⊗ₜ[K] c) =
      M.left a (f (b ⊗ₜ[K] c)) - f ((a * b) ⊗ₜ[K] c) +
      f (a ⊗ₜ[K] (b * c)) - M.right (f (a ⊗ₜ[K] b)) c := by
  change barEquiv K A P 2 (delta M 2 f) (a ⊗ₜ[K] b) c = _
  rw [bar_delta, delta_one_apply]
  change M.left a (f (b ⊗ₜ[K] c)) - f ((a * b) ⊗ₜ[K] c) +
    (f (a ⊗ₜ[K] (b * c)) - M.right (f (a ⊗ₜ[K] b)) c) = _
  abel

namespace Extension

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

/-- The bilinear defect of a linear section takes values in the extension kernel. -/
def sectionDefect (E : Extension K A B) (ρ : A →ₗ[K] B)
    (hρ : ∀ a, E.sigma (ρ a) = a) : A →ₗ[K] A →ₗ[K] E.kernel :=
  LinearMap.mk₂ K (fun a b => ⟨ρ a * ρ b - ρ (a * b), by
    change E.sigma (ρ a * ρ b - ρ (a * b)) = 0
    simp [map_sub, map_mul, hρ]⟩)
    (by intros; apply Subtype.ext; simp [add_mul]; abel)
    (by intros; apply Subtype.ext; simp [smul_mul_assoc, smul_sub])
    (by intros; apply Subtype.ext; simp [mul_add]; abel)
    (by intros; apply Subtype.ext; simp [mul_smul_comm, smul_sub])

/-- **Construction (unnumbered, p. 66, 1)** (Hochschild). The section gives
exactly the source two-cochain `ρ(a)ρ(b) - ρ(ab)`, viewed on the tensor product. -/
def sectionCocycle (E : Extension K A B) (ρ : A →ₗ[K] B)
    (hρ : ∀ a, E.sigma (ρ a) = a) : Cochain K A E.kernel 2 :=
  TensorProduct.lift (sectionDefect E ρ hρ)

/-- Evaluation is the printed defect formula, with values in the kernel. -/
@[simp] theorem sectionCocycle_apply (E : Extension K A B) (ρ : A →ₗ[K] B)
    (hρ : ∀ a, E.sigma (ρ a) = a) (a b : A) :
    (sectionCocycle E ρ hρ (a ⊗ₜ[K] b) : B) = ρ a * ρ b - ρ (a * b) := rfl

/-- **Construction (unnumbered, p. 66, 1) (cocycle)** (Hochschild).
Expanding the four terms cancels by associativity, the source's direct verification. -/
theorem sectionCocycle_isCocycle (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    IsCocycle (E.kernelModule hE ρ hρ) 2 (sectionCocycle E ρ hρ) := by
  apply TensorProduct.ext_threefold
  intro a b c
  rw [delta_two_apply]
  apply Subtype.ext
  change ρ a * (ρ b * ρ c - ρ (b * c)) -
    (ρ (a * b) * ρ c - ρ ((a * b) * c)) +
    (ρ a * ρ (b * c) - ρ (a * (b * c))) -
    (ρ a * ρ b - ρ (a * b)) * ρ c = 0
  simp only [mul_sub, sub_mul, mul_assoc]
  abel

/-- The difference of two linear sections is a one-cochain with values in the kernel. -/
def sectionDifference (E : Extension K A B) (ρ τ : A →ₗ[K] B)
    (hρ : ∀ a, E.sigma (ρ a) = a) (hτ : ∀ a, E.sigma (τ a) = a) :
    Cochain K A E.kernel 1 :=
  (ρ - τ).codRestrict E.kernel (by intro a; change E.sigma (ρ a - τ a) = 0; simp [hρ, hτ])

/-- The source's displayed calculation: changing the section changes its
cocycle by the coboundary of the difference of the sections. -/
theorem sectionCocycle_sub (E : Extension K A B) (hE : E.IsSingular)
    (ρ τ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (hτ : ∀ a, E.sigma (τ a) = a) :
    sectionCocycle E ρ hρ - sectionCocycle E τ hτ =
      delta (E.kernelModule hE ρ hρ) 1 (sectionDifference E ρ τ hρ hτ) := by
  apply TensorProduct.ext'
  intro a b
  rw [delta_one_apply]
  apply Subtype.ext
  change (ρ a * ρ b - ρ (a * b)) - (τ a * τ b - τ (a * b)) =
    ρ a * (ρ b - τ b) - (ρ (a * b) - τ (a * b)) + (ρ a - τ a) * ρ b
  have ha : E.sigma (ρ a - τ a) = 0 := by simp [hρ, hτ]
  have hb : E.sigma (ρ b - τ b) = 0 := by simp [hρ, hτ]
  have hz := hE (ρ a - τ a) (ρ b - τ b) ha hb
  rw [mul_sub] at hz
  rw [sub_eq_zero.mp hz]
  simp only [mul_sub, sub_mul]
  abel

/-- **Construction (unnumbered, p. 66, 1) (section independence)** (Hochschild).
The two section cocycles are cohomologous; their difference is an actual coboundary. -/
theorem sectionCocycle_cohomologous (E : Extension K A B) (hE : E.IsSingular)
    (ρ τ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (hτ : ∀ a, E.sigma (τ a) = a) :
    IsCoboundary (E.kernelModule hE ρ hρ) 1
      (sectionCocycle E ρ hρ - sectionCocycle E τ hτ) :=
  ⟨sectionDifference E ρ τ hρ hτ, sectionCocycle_sub E hE ρ τ hρ hτ⟩

end Extension
end Hochschild1945
