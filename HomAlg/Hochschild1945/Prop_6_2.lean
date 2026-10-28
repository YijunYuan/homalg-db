import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Con_cocycle_extension
import HomAlg.Hochschild1945.Con_extension_cocycle
import HomAlg.Hochschild1945.Con_extension_module
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_isomorphic_extensions

/-!
```yaml node
id: "Hochschild1945.Prop_6_2"
doc: "Hochschild1945"
kind: "proposition"
source:
  label: "Proposition 6.2"
  pages:
    - 65
    - 66
    - 67
  chapter: "6"
tags:
  - "hochschild-cohomology"
  - "singular-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Con_cocycle_extension"
    - "Hochschild1945.Con_extension_cocycle"
    - "Hochschild1945.Con_extension_module"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_extension"
    - "Hochschild1945.Def_isomorphic_extensions"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Con_cocycle_extension"
    - "Hochschild1945.Con_extension_cocycle"
    - "Hochschild1945.Con_extension_module"
decls:
  - "Hochschild1945.singular_extensions_classified_by_cohomology"
  - "Hochschild1945.CocycleExtension.realizes_every_cohomology_class"
fidelity:
  status: "faithful"
  reviewed:
    by: "schema-taxonomy"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.singular_extensions_classified_by_cohomology:
        statement_sha256: "71e9f0b3c9199a52ca915c2079ee0544a295c5eff9fe6df3fb5df1b8e14d12f5"
        type_hash: "0000000066d019fe"
        meaning_hash: "802f5b671f4b206b"
      Hochschild1945.CocycleExtension.realizes_every_cohomology_class:
        statement_sha256: "511866f26861e02d36052f4c5a6f997e45814f0cafd24014ab374c9a2c563f9a"
        type_hash: "0000000086c6ac5c"
        meaning_hash: "ba8d53a2cb61320c"
    session: "schema-taxonomy-prop62-independent"
    author_session: "root-and-ci-prop62-2026-10-28"
    note: "Independent pp65–67 image comparison, both principal statements and proofs, genuine representative
      classification and realization; axiom closure has no sorryAx."
title: "Classification of singular extensions"
```

## Statement

There is a one to one correspondence between the classes of isomorphic singular extensions, and the 2-dimensional cohomology classes of $\mathfrak{A}$. (We identify corresponding cohomology classes over operator-isomorphic $\mathfrak{A}$-modules.)

## Proof

Let $\{\mathfrak{B},\sigma\}$ be a singular extension of $\mathfrak{A}$ with kernel $\mathfrak{K}$. Let $\rho$ be any linear mapping of $\mathfrak{A}$ into $\mathfrak{B}$ such that
\[
\sigma\{\rho\{a\}\}=a,\quad\hbox{for every } a\in\mathfrak{A},\quad\hbox{or---which is equivalent---}
\]
\begin{equation}\tag{1}
\rho\{\sigma\{b\}\}\equiv b\bmod\mathfrak{K},\quad\hbox{for every }b\in\mathfrak{B}.
\end{equation}

We can make $\mathfrak{K}$ a two-sided $\mathfrak{A}$-module by the definitions $a\cdot k=\rho\{a\}k$, $k\cdot a=k\rho\{a\}$, where $k\in\mathfrak{K}$, $a\in\mathfrak{A}$. Since the difference of any two mappings $\rho$ satisfying (1) is a mapping of $\mathfrak{A}$ into $\mathfrak{K}$ and since $\mathfrak{K}^2=\{0\}$ it is clear that $k\cdot a$ and $a\cdot k$ are independent of the particular mapping $\rho$ we have selected. Thus the two-sided $\mathfrak{A}$-module $\mathfrak{K}$ is uniquely determined by the extension $\{\mathfrak{B},\sigma\}$. Furthermore, if $\{\mathfrak{B}^*,\sigma^*\}$ is an isomorphic extension, we have:
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
This means that $I$ is an operator isomorphism between the two-sided $\mathfrak{A}$-modules $\mathfrak{K}$ and $\mathfrak{K}^*$, and we have shown that isomorphic extensions lead to operator-isomorphic $\mathfrak{A}$-modules. [uses `Hochschild1945.Con_extension_module`]

Consider now the mapping $a_1\times a_2\to f_\rho\{a_1,a_2\}=\rho\{a_1\}\rho\{a_2\}-\rho\{a_1a_2\}$ of $\mathfrak{A}\times\mathfrak{A}$ into $\mathfrak{K}$. It is easy to verify that $f_\rho$ is a $(2,\mathfrak{K})$-cocycle of $\mathfrak{A}$.

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
i.e. $f_\rho-f_{\rho'}=\delta(\rho-\rho')$. Hence the cohomology class $\bar f$ of $f_\rho$ is uniquely determined by the extension $\{\mathfrak{B},\sigma\}$. [uses `Hochschild1945.Con_extension_cocycle`]

Now let $\{\mathfrak{B}^*,\sigma^*\}$ be a singular extension of $\mathfrak{A}$ which is isomorphic (by the isomorphism $I$) with $\{\mathfrak{B},\sigma\}$. Then $I\rho$ is clearly a linear mapping of $\mathfrak{A}$ into $\mathfrak{B}^*$ which satisfies (1). Hence $f_{I\rho}$ is a $(2,\mathfrak{K}^*)$-cocycle of $\mathfrak{A}$ which lies in the cohomology class determined by the extension $\{\mathfrak{B}^*,\sigma^*\}$. Since $f_{I\rho}=If_\rho$, the cohomology class determined by the extension $\{\mathfrak{B}^*,\sigma^*\}$ is the isomorphic image by $I$ of the cohomology class determined by $\{\mathfrak{B},\sigma\}$.

Conversely, suppose that we are given a two-sided $\mathfrak{A}$-module $\mathfrak{P}$ and a $(2,\mathfrak{P})$-cocycle $f$ of $\mathfrak{A}$. Let $\mathfrak{B}$ be the direct sum of the linear space underlying $\mathfrak{A}$ and the linear space $\mathfrak{P}$. Let $(a_1,u_1)$, $(a_2,u_2)$ ($a_i\in\mathfrak{A}$, $u_i\in\mathfrak{P}$) be any two elements of $\mathfrak{B}$. We define their product by the equation $(a_1,u_1)(a_2,u_2)=(a_1a_2,a_1\cdot u_2+u_1\cdot a_2+f\{a_1,a_2\})$. Using the fact that $f$ is a cocycle we verify easily that this multiplication is associative. Hence $\mathfrak{B}$ has been given the structure of an algebra, $\mathfrak{B}_f$, say. The mapping $(a,u)\to\sigma\{(a,u)\}=a$ is obviously a homomorphism of $\mathfrak{B}_f$ onto $\mathfrak{A}$. The kernel of $\sigma$ is the ideal $\mathfrak{K}=(0,\mathfrak{P})$ of $\mathfrak{B}_f$ and, clearly, $\mathfrak{K}^2=\{0\}$. Thus $\{\mathfrak{B}_f,\sigma\}$ is a singular extension of $\mathfrak{A}$. Moreover, if $\rho$ is the mapping $a\to(a,0)$ of $\mathfrak{A}$ into $\mathfrak{B}_f$, $\rho$ satisfies condition (1) and the $(2,\mathfrak{K})$-cocycle $f_\rho$ derived from the extension $\{\mathfrak{B}_f,\sigma\}$ and $\rho$ is (to within a trivial isomorphism) identical with $f$. It is obvious that if $f$ and $f^*$ are corresponding cocycles over operator-isomorphic $\mathfrak{A}$-modules the corresponding extensions of $\mathfrak{A}$ are isomorphic.

Finally, let $f'$ be another $(2,\mathfrak{P})$-cocycle of $\mathfrak{A}$ which is cohomologous to $f$. Then there exists a linear mapping $\tau$ of $\mathfrak{A}$ into $\mathfrak{P}$ such that $f-f'=\delta\tau$, i.e. [uses `Hochschild1945.Def_2_1`]
\[
f\{a_1,a_2\}=f'\{a_1,a_2\}+a_1\cdot\tau\{a_2\}-\tau\{a_1a_2\}+\tau\{a_1\}\cdot a_2.
\]
Consider the mapping $(a,u)\to I\{(a,u)\}=(a,u+\tau\{a\})$ of $\mathfrak{B}_f$ onto $\mathfrak{B}_{f'}$. We have:

\[
\begin{aligned}
I\{(a_1,u_1)(a_2,u_2)\}
&=(a_1a_2,a_1\cdot u_2+u_1\cdot a_2+f\{a_1,a_2\}+\tau\{a_1a_2\})\\
&=(a_1a_2,a_1\cdot u_2+u_1\cdot a_2+a_1\cdot\tau\{a_2\}+\tau\{a_1\}\cdot a_2+f'\{a_1,a_2\})\\
&=(a_1,u_1+\tau\{a_1\})(a_2,u_2+\tau\{a_2\})=I\{(a_1,u_1)\}I\{(a_2,u_2)\},
\end{aligned}
\]
i.e. $I$ is an isomorphism of $\mathfrak{B}_f$ onto $\mathfrak{B}_{f'}$. Moreover,
\[
\sigma'\{I\{(a,u)\}\}=\sigma'\{(a,u+\tau\{a\})\}=a=\sigma\{(a,u)\}.
\]
Hence the extensions $\{\mathfrak{B}_f,\sigma\}$ and $\{\mathfrak{B}_{f'},\sigma'\}$ are isomorphic. [uses `Hochschild1945.Con_cocycle_extension`] We state the foregoing results in the following proposition:

## Description

Matches singular extension classes with degree-two cohomology classes, identifying classes over isomorphic bimodules.

## Formalization notes

The proof consists of the three preceding constructions on pages 65–67. The equivalence identifies cohomology classes over operator-isomorphic coefficient modules, not only classes for a fixed module.

The classification is expressed on representatives: two arbitrary singular
extensions have the same isomorphism class exactly when an operator isomorphism
identifies their cocycles modulo an actual source coboundary. The second principal
theorem realizes every two-cocycle and recovers it through the kernel operator
isomorphism. Together these state injectivity and surjectivity of the printed
correspondence, including its parenthetical identification across coefficient
modules. No artificial quotient of all Lean types is used. Both the realization proof
and classification equivalence are complete. A section gives an actual linear
equivalence B ≃ A × ker(σ); its multiplication is the source cocycle product.
An operator isomorphism followed by the source shear (a,k) ↦ (a,Ik+g(a)) is
multiplicative precisely under the displayed coboundary equation. Composing
these concrete coordinate equivalences reconstructs the extension isomorphism.
Conversely, naturality of section cocycles and independence of the section give
the required coboundary difference.


Def_2_3 is retained as the source statement's reference to cohomology classes.
The two principal declarations express classification and realization on actual
cocycle representatives modulo IsCoboundary, as explained above, so they do not
directly mention the Cohomology quotient constant from Def_2_3. This accounts
for `deps_diff.declared_not_verified.statement` without constructing an artificial
quotient of all coefficient types. In contrast, Def_2_1 is a genuine compiled
proof dependency: cohomologyCoordinates_mul expands delta_one_apply to verify
the multiplicativity of the source coboundary shear.

-/

namespace Hochschild1945
universe u
variable {K A B C : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]
  [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]

namespace Extension

/-- A linear section identifies the extension vector space with A plus its kernel. -/
def sectionCoordinates (E : Extension K A B) (ρ : A →ₗ[K] B)
    (hρ : ∀ a, E.sigma (ρ a) = a) : B ≃ₗ[K] A × E.kernel where
  toFun b := (E.sigma b, ⟨b - ρ (E.sigma b), by simp [hρ]⟩)
  invFun x := ρ x.1 + x.2
  left_inv b := by simp
  right_inv x := by
    apply Prod.ext
    · change E.sigma (ρ x.1 + x.2) = x.1
      simp [hρ, show E.sigma (x.2 : B) = 0 from x.2.property]
    · apply Subtype.ext
      change ρ x.1 + (x.2 : B) - ρ (E.sigma (ρ x.1 + x.2)) = x.2
      simp [hρ, show E.sigma (x.2 : B) = 0 from x.2.property]
  map_add' b c := by
    apply Prod.ext
    · simp
    · apply Subtype.ext
      simp only [map_add, Prod.snd_add, Submodule.coe_add]
      abel
  map_smul' r b := by
    apply Prod.ext
    · simp
    · apply Subtype.ext
      simp [smul_sub]

/-- Multiplication written in the source's section and kernel coordinates. -/
def coordinateMul (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (x y : A × E.kernel) : A × E.kernel :=
  (x.1*y.1, (E.kernelModule hE ρ hρ).left x.1 y.2 +
    (E.kernelModule hE ρ hρ).right x.2 y.1 + E.sectionCocycle ρ hρ (x.1 ⊗ₜ[K] y.1))

/-- The multiplication of every singular extension is its section cocycle product. -/
theorem sectionCoordinates_mul (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) (b c : B) :
    sectionCoordinates E ρ hρ (b*c) = coordinateMul E hE ρ hρ
      (sectionCoordinates E ρ hρ b) (sectionCoordinates E ρ hρ c) := by
  apply Prod.ext
  · exact map_mul E.sigma b c
  · apply Subtype.ext
    change b*c - ρ (E.sigma (b*c)) =
      ρ (E.sigma b) * (c - ρ (E.sigma c)) +
      (b - ρ (E.sigma b)) * ρ (E.sigma c) +
      (ρ (E.sigma b) * ρ (E.sigma c) - ρ (E.sigma b * E.sigma c))
    have hb : E.sigma (b - ρ (E.sigma b)) = 0 := by simp [hρ]
    have hc : E.sigma (c - ρ (E.sigma c)) = 0 := by simp [hρ]
    have hz := hE _ _ hb hc
    simp only [sub_mul, mul_sub] at hz ⊢
    rw [map_mul]
    linear_combination (norm := abel) hz

/-- Operator transport followed by the source's coboundary coordinate change. -/
def cohomologyCoordinates (E : Extension K A B) (F : Extension K A C)
    (I : E.kernel ≃ₗ[K] F.kernel) (g : A →ₗ[K] F.kernel) :
    (A × E.kernel) ≃ₗ[K] (A × F.kernel) where
  toFun x := (x.1, I x.2 + g x.1)
  invFun x := (x.1, I.symm (x.2 - g x.1))
  left_inv x := by apply Prod.ext <;> simp
  right_inv x := by apply Prod.ext <;> simp
  map_add' x y := by
    apply Prod.ext
    · rfl
    · change I (x.2+y.2) + g (x.1+y.1) = (I x.2 + g x.1) + (I y.2 + g y.1)
      rw [map_add, map_add]
      abel
  map_smul' r x := by
    apply Prod.ext
    · rfl
    · change I (r • x.2) + g (r • x.1) = r • (I x.2 + g x.1)
      simp only [map_smul, smul_add]

/-- The coordinate change preserves multiplication exactly when the cocycles
are related by the source coboundary equation. -/
theorem cohomologyCoordinates_mul (E : Extension K A B) (F : Extension K A C)
    (hE : E.IsSingular) (hF : F.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (σ : A →ₗ[K] C) (hσ : ∀ a, F.sigma (σ a) = a)
    (I : E.kernel ≃ₗ[K] F.kernel)
    (hl : ∀ a k, I ((E.kernelModule hE ρ hρ).left a k) = (F.kernelModule hF σ hσ).left a (I k))
    (hr : ∀ k a, I ((E.kernelModule hE ρ hρ).right k a) = (F.kernelModule hF σ hσ).right (I k) a)
    (g : A →ₗ[K] F.kernel)
    (hg : I.toLinearMap.comp (E.sectionCocycle ρ hρ) - F.sectionCocycle σ hσ =
      delta (F.kernelModule hF σ hσ) 1 g) (x y : A × E.kernel) :
    cohomologyCoordinates E F I g (coordinateMul E hE ρ hρ x y) =
      coordinateMul F hF σ hσ (cohomologyCoordinates E F I g x) (cohomologyCoordinates E F I g y) := by
  apply Prod.ext
  · rfl
  · have h := LinearMap.congr_fun hg (x.1 ⊗ₜ[K] y.1)
    rw [delta_one_apply] at h
    change I (E.sectionCocycle ρ hρ (x.1 ⊗ₜ[K] y.1)) - F.sectionCocycle σ hσ (x.1 ⊗ₜ[K] y.1) =
      (F.kernelModule hF σ hσ).left x.1 (g y.1) - g (x.1*y.1) +
      (F.kernelModule hF σ hσ).right (g x.1) y.1 at h
    change I ((E.kernelModule hE ρ hρ).left x.1 y.2 +
      (E.kernelModule hE ρ hρ).right x.2 y.1 + E.sectionCocycle ρ hρ (x.1 ⊗ₜ[K] y.1)) + g (x.1*y.1) =
      (F.kernelModule hF σ hσ).left x.1 (I y.2 + g y.1) +
      (F.kernelModule hF σ hσ).right (I x.2 + g x.1) y.1 + F.sectionCocycle σ hσ (x.1 ⊗ₜ[K] y.1)
    simp only [map_add, LinearMap.add_apply, hl, hr]
    linear_combination (norm := abel) h

/-- Reconstruct an extension isomorphism from an operator isomorphism and a
primitive of the difference of the transported section cocycles. -/
def isomorphismOfCohomology (E : Extension K A B) (F : Extension K A C)
    (hE : E.IsSingular) (hF : F.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (σ : A →ₗ[K] C) (hσ : ∀ a, F.sigma (σ a) = a)
    (I : E.kernel ≃ₗ[K] F.kernel)
    (hl : ∀ a k, I ((E.kernelModule hE ρ hρ).left a k) = (F.kernelModule hF σ hσ).left a (I k))
    (hr : ∀ k a, I ((E.kernelModule hE ρ hρ).right k a) = (F.kernelModule hF σ hσ).right (I k) a)
    (g : A →ₗ[K] F.kernel)
    (hg : I.toLinearMap.comp (E.sectionCocycle ρ hρ) - F.sectionCocycle σ hσ =
      delta (F.kernelModule hF σ hσ) 1 g) : Isomorphism E F := by
  let e := (sectionCoordinates E ρ hρ).trans
    ((cohomologyCoordinates E F I g).trans (sectionCoordinates F σ hσ).symm)
  have he (b : B) : sectionCoordinates F σ hσ (e b) =
      cohomologyCoordinates E F I g (sectionCoordinates E ρ hρ b) := by simp [e]
  exact {
    toLinearEquiv := e
    commutes := by
      intro b
      have hh := congrArg Prod.fst (he b)
      exact hh
    map_mul' := by
      intro b c
      apply (sectionCoordinates F σ hσ).injective
      rw [he, sectionCoordinates_mul F hF σ hσ, he, he, sectionCoordinates_mul E hE ρ hρ]
      exact cohomologyCoordinates_mul E F hE hF ρ hρ σ hσ I hl hr g hg _ _ }

/-- Section cocycles are natural under an actual isomorphism of extensions. -/
theorem Isomorphism.sectionCocycle_natural {E : Extension K A B} {F : Extension K A C}
    (J : Isomorphism E F) (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    let τ := J.toLinearEquiv.toLinearMap.comp ρ
    let hτ : ∀ a, F.sigma (τ a) = a := fun a => (J.commutes (ρ a)).trans (hρ a)
    F.sectionCocycle τ hτ = J.kernelEquiv.toLinearMap.comp (E.sectionCocycle ρ hρ) := by
  apply TensorProduct.ext'
  intro a b
  apply Subtype.ext
  change J.toLinearEquiv (ρ a) * J.toLinearEquiv (ρ b) - J.toLinearEquiv (ρ (a*b)) =
    J.toLinearEquiv (ρ a * ρ b - ρ (a*b))
  rw [map_sub, J.map_mul']

end Extension

/-- **Proposition 6.2** (Hochschild), equality of classes. Two singular extensions
are isomorphic precisely when an operator isomorphism of their coefficient
modules identifies their degree-two cohomology classes. The class equality is
written as an actual coboundary difference, the quotient relation of Definition
2.3. Recover each extension from its section and defect, and use the source's
change-of-coordinates map for the converse. -/
theorem singular_extensions_classified_by_cohomology
    (E : Extension K A B) (F : Extension K A C)
    (hE : E.IsSingular) (hF : F.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (σ : A →ₗ[K] C) (hσ : ∀ a, F.sigma (σ a) = a) :
    E.Isomorphic F ↔ ∃ I : E.kernel ≃ₗ[K] F.kernel,
      (∀ a k, I ((E.kernelModule hE ρ hρ).left a k) =
        (F.kernelModule hF σ hσ).left a (I k)) ∧
      (∀ k a, I ((E.kernelModule hE ρ hρ).right k a) =
        (F.kernelModule hF σ hσ).right (I k) a) ∧
      IsCoboundary (F.kernelModule hF σ hσ) 1
        (I.toLinearMap.comp (E.sectionCocycle ρ hρ) - F.sectionCocycle σ hσ) := by
  constructor
  · rintro ⟨J⟩
    refine ⟨J.kernelEquiv, J.kernelEquiv_left hE ρ σ hρ hσ,
      J.kernelEquiv_right hE ρ σ hρ hσ, ?_⟩
    let τ := J.toLinearEquiv.toLinearMap.comp ρ
    have hτ : ∀ a, F.sigma (τ a) = a := fun a => (J.commutes (ρ a)).trans (hρ a)
    have hn := J.sectionCocycle_natural ρ hρ
    change F.sectionCocycle τ hτ = J.kernelEquiv.toLinearMap.comp (E.sectionCocycle ρ hρ) at hn
    rw [← hn]
    have hc := F.sectionCocycle_cohomologous hF τ σ hτ hσ
    rw [F.kernelModule_independent hF τ σ hτ hσ] at hc
    exact hc
  · rintro ⟨I,hl,hr,g,hg⟩
    exact ⟨Extension.isomorphismOfCohomology E F hE hF ρ hρ σ hσ I hl hr g hg⟩

namespace CocycleExtension
attribute [local instance] addCommGroupStructure moduleStructure mulStructure
variable {P : Type u} [AddCommGroup P] [Module K P]
variable (M : TwoSidedModule K A P) (f : Cochain K A P 2)

/-- The source's canonical linear lift a ↦ (a,0) in the constructed extension. -/
def canonicalSection : A →ₗ[K] CocycleExtension M f where
  toFun a := ⟨a, 0⟩
  map_add' := by intros; ext <;> simp
  map_smul' := by intros; ext <;> simp

/-- The kernel of the cocycle extension is the original coefficient module. -/
def kernelEquivCoefficients (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    (extension M f hf).kernel ≃ₗ[K] P := by
  letI := ring M f hf
  letI := scalarTower M f hf
  letI := smulComm M f hf
  exact {
    toFun := fun k => k.val.snd
    invFun := fun p => ⟨⟨0,p⟩, rfl⟩
    left_inv := by
      intro k
      apply Subtype.ext
      apply ext
      · exact k.property.symm
      · rfl
    right_inv := fun _ => rfl
    map_add' := fun _ _ => rfl
    map_smul' := fun _ _ => rfl }

/-- The canonical lift is a section of the original projection. -/
theorem canonicalSection_section (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    ∀ a, (extension M f hf).sigma (canonicalSection M f a) = a := by
  intros
  rfl

/-- **Proposition 6.2** (Hochschild), existence of every class. The source
extension constructed from any two-cocycle recovers that cocycle, with an
operator isomorphism from its kernel to the original coefficient module.
Projection onto the second coordinate gives the isomorphism; multiplying the
canonical lifts gives exactly f. -/
theorem realizes_every_cohomology_class (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    let E := extension M f hf
    let hE := extension_singular M f hf
    let ρ := canonicalSection M f
    let hρ := canonicalSection_section M f hf
    ∃ I : E.kernel ≃ₗ[K] P,
      (∀ a k, I ((E.kernelModule hE ρ hρ).left a k) = M.left a (I k)) ∧
      (∀ k a, I ((E.kernelModule hE ρ hρ).right k a) = M.right (I k) a) ∧
      I.toLinearMap.comp (E.sectionCocycle ρ hρ) = f := by
  letI := ring M f hf
  letI := scalarTower M f hf
  letI := smulComm M f hf
  refine ⟨kernelEquivCoefficients M f hf, ?_, ?_, ?_⟩
  · intro a k
    change (mul M f (canonicalSection M f a) k.val).snd = M.left a k.val.snd
    have hk : k.val.fst = 0 := k.property
    simp [mul, canonicalSection, hk]
  · intro k a
    change (mul M f k.val (canonicalSection M f a)).snd = M.right k.val.snd a
    have hk : k.val.fst = 0 := k.property
    simp [mul, canonicalSection, hk]
  · apply TensorProduct.ext'
    intro a b
    change (mul M f (canonicalSection M f a) (canonicalSection M f b)).snd -
      (canonicalSection M f (a*b)).snd = f (TensorProduct.tmul K a b)
    simp [mul, canonicalSection]

end CocycleExtension
end Hochschild1945
