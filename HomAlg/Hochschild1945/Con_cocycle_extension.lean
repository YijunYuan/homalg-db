import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_extension_cocycle
import Mathlib.Tactic.LinearCombination
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Def_isomorphic_extensions

/-!
```yaml node
id: "Hochschild1945.Con_cocycle_extension"
doc: "Hochschild1945"
kind: "construction"
source:
  label: "Construction (unnumbered, p. 66, 2)"
  pages:
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
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_extension"
    - "Hochschild1945.Def_isomorphic_extensions"
    - "Hochschild1945.Def_two_sided_module"
  proof:
    - "Hochschild1945.Con_extension_cocycle"
decls:
  - "Hochschild1945.CocycleExtension.mul"
  - "Hochschild1945.CocycleExtension.ring"
  - "Hochschild1945.CocycleExtension.extension"
  - "Hochschild1945.CocycleExtension.extension_singular"
  - "Hochschild1945.CocycleExtension.cohomologous_isomorphic"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.CocycleExtension.mul:
        statement_sha256: "6aee05b599e0e4a31cfe5be59f798a61117b27df6d39aacb39734b0faab3756c"
        type_hash: "00000000e7eb6f77"
        meaning_hash: "78a11bbdd0418cef"
      Hochschild1945.CocycleExtension.ring:
        statement_sha256: "e71375f94971d4a0ccd135ea4faee5a2a0690f031fdcd4d69c85a802b4afc08e"
        type_hash: "000000008343496e"
        meaning_hash: "ddee386e56f373d4"
      Hochschild1945.CocycleExtension.extension:
        statement_sha256: "b54251fe64c3e8450bcdddfba00f77b8b3c91be9b1e7b1bca23cf1c451c1354f"
        type_hash: "000000000796e9e4"
        meaning_hash: "560cda4806cff038"
      Hochschild1945.CocycleExtension.extension_singular:
        statement_sha256: "47da293ba502df16b9fe4184b1557deec4cc3cadc7782d5026d9e2d8072f5ba1"
        type_hash: "00000000daecd851"
        meaning_hash: "ca876576aa418408"
      Hochschild1945.CocycleExtension.cohomologous_isomorphic:
        statement_sha256: "ac49ee8f86ff5224f69fa5eca1ec3e3a9dd0647daae191137f822338bb069ed8"
        type_hash: "00000000e97813de"
        meaning_hash: "e382ded10ad5a52c"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Singular extension associated with a cocycle"
```

## Statement

Conversely, suppose that we are given a two-sided $\mathfrak{A}$-module $\mathfrak{P}$ and a $(2,\mathfrak{P})$-cocycle $f$ of $\mathfrak{A}$. Let $\mathfrak{B}$ be the direct sum of the linear space underlying $\mathfrak{A}$ and the linear space $\mathfrak{P}$. Let $(a_1,u_1)$, $(a_2,u_2)$ ($a_i\in\mathfrak{A}$, $u_i\in\mathfrak{P}$) be any two elements of $\mathfrak{B}$. We define their product by the equation $(a_1,u_1)(a_2,u_2)=(a_1a_2,a_1\cdot u_2+u_1\cdot a_2+f\{a_1,a_2\})$. Using the fact that $f$ is a cocycle we verify easily that this multiplication is associative. Hence $\mathfrak{B}$ has been given the structure of an algebra, $\mathfrak{B}_f$, say. The mapping $(a,u)\to\sigma\{(a,u)\}=a$ is obviously a homomorphism of $\mathfrak{B}_f$ onto $\mathfrak{A}$. The kernel of $\sigma$ is the ideal $\mathfrak{K}=(0,\mathfrak{P})$ of $\mathfrak{B}_f$ and, clearly, $\mathfrak{K}^2=\{0\}$. Thus $\{\mathfrak{B}_f,\sigma\}$ is a singular extension of $\mathfrak{A}$. Moreover, if $\rho$ is the mapping $a\to(a,0)$ of $\mathfrak{A}$ into $\mathfrak{B}_f$, $\rho$ satisfies condition (1) and the $(2,\mathfrak{K})$-cocycle $f_\rho$ derived from the extension $\{\mathfrak{B}_f,\sigma\}$ and $\rho$ is (to within a trivial isomorphism) identical with $f$. It is obvious that if $f$ and $f^*$ are corresponding cocycles over operator-isomorphic $\mathfrak{A}$-modules the corresponding extensions of $\mathfrak{A}$ are isomorphic.

## Proof

Finally, let $f'$ be another $(2,\mathfrak{P})$-cocycle of $\mathfrak{A}$ which is cohomologous to $f$. Then there exists a linear mapping $\tau$ of $\mathfrak{A}$ into $\mathfrak{P}$ such that $f-f'=\delta\tau$, i.e.
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
Hence the extensions $\{\mathfrak{B}_f,\sigma\}$ and $\{\mathfrak{B}_{f'},\sigma'\}$ are isomorphic. We state the foregoing results in the following proposition:

[uses `Hochschild1945.Con_extension_cocycle`]

## Description

Constructs a singular extension from a two-cocycle and an isomorphism between extensions of cohomologous cocycles.
-/

namespace Hochschild1945

universe u
open scoped TensorProduct

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P]

/-- The source's direct-sum vector space, tagged by its module and cocycle so
that different cocycle multiplications have distinct carriers. -/
structure CocycleExtension (M : TwoSidedModule K A P) (f : Cochain K A P 2) extends A × P

namespace CocycleExtension

variable (M : TwoSidedModule K A P) (f : Cochain K A P 2)

/-- Forget only the cocycle tag, retaining both coordinates. -/
def equiv : CocycleExtension M f ≃ A × P where
  toFun := toProd
  invFun := mk
  left_inv _ := rfl
  right_inv _ := rfl

/-- The additive group is transported from the original direct-sum vector space. -/
abbrev addCommGroupStructure : AddCommGroup (CocycleExtension M f) := (equiv M f).addCommGroup

attribute [local instance] addCommGroupStructure

/-- Its additive operations are exactly the direct-sum vector-space operations. -/
def addEquiv : CocycleExtension M f ≃+ A × P where
  __ := equiv M f
  map_add' _ _ := rfl

/-- Scalar multiplication is the original coordinate-wise K-action. -/
abbrev moduleStructure : Module K (CocycleExtension M f) := (addEquiv M f).module K

attribute [local instance] moduleStructure

/-- The original direct sum as a linear equivalence. -/
def linearEquiv : CocycleExtension M f ≃ₗ[K] A × P := (addEquiv M f).linearEquiv K

/-- Two cocycle-extension vectors are equal when both coordinates agree. -/
@[ext] theorem ext {x y : CocycleExtension M f}
    (h₁ : x.fst = y.fst) (h₂ : x.snd = y.snd) : x = y := by
  apply (equiv M f).injective
  exact Prod.ext h₁ h₂

/-- The algebra coordinate of zero vanishes. -/
@[simp] theorem fst_zero : (0 : CocycleExtension M f).fst = 0 := rfl
/-- The coefficient coordinate of zero vanishes. -/
@[simp] theorem snd_zero : (0 : CocycleExtension M f).snd = 0 := rfl
/-- Projection onto A preserves addition. -/
@[simp] theorem fst_add (x y : CocycleExtension M f) : (x+y).fst = x.fst+y.fst := rfl
/-- Projection onto the coefficient space preserves addition. -/
@[simp] theorem snd_add (x y : CocycleExtension M f) : (x+y).snd = x.snd+y.snd := rfl
/-- Projection onto A preserves scalar multiplication. -/
@[simp] theorem fst_smul (r : K) (x : CocycleExtension M f) : (r • x).fst = r • x.fst := rfl
/-- Projection onto the coefficient space preserves scalar multiplication. -/
@[simp] theorem snd_smul (r : K) (x : CocycleExtension M f) : (r • x).snd = r • x.snd := rfl

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), multiplication.
The cocycle contributes precisely the additional kernel coordinate. -/
def mul (x y : CocycleExtension M f) : CocycleExtension M f :=
  ⟨x.fst*y.fst, M.left x.fst y.snd + M.right x.snd y.fst + f (x.fst ⊗ₜ[K] y.fst)⟩

/-- Install the source cocycle multiplication on its tagged carrier. -/
abbrev mulStructure : Mul (CocycleExtension M f) := ⟨mul M f⟩

attribute [local instance] mulStructure

/-- The algebra coordinate multiplies in A. -/
@[simp] theorem fst_mul (x y : CocycleExtension M f) : (x*y).fst = x.fst*y.fst := rfl
/-- The coefficient coordinate is the source action sum plus the cocycle. -/
@[simp] theorem snd_mul (x y : CocycleExtension M f) :
    (x*y).snd = M.left x.fst y.snd + M.right x.snd y.fst + f (x.fst ⊗ₜ[K] y.fst) := rfl

/-- The two-cocycle equation, in exactly the order needed for associativity. -/
theorem cocycle_equation (hf : IsCocycle M 2 f) (a b c : A) :
    f ((a*b) ⊗ₜ[K] c) + M.right (f (a ⊗ₜ[K] b)) c =
      M.left a (f (b ⊗ₜ[K] c)) + f (a ⊗ₜ[K] (b*c)) := by
  have h := LinearMap.congr_fun hf ((a ⊗ₜ[K] b) ⊗ₜ[K] c)
  rw [delta_two_apply] at h
  change M.left a (f (b ⊗ₜ[K] c)) - f ((a*b) ⊗ₜ[K] c) +
    f (a ⊗ₜ[K] (b*c)) - M.right (f (a ⊗ₜ[K] b)) c = 0 at h
  linear_combination (norm := abel) -h

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), algebra laws.
Associativity follows from the cocycle equation and the three module laws. -/
abbrev ring (hf : IsCocycle M 2 f) : NonUnitalRing (CocycleExtension M f) where
  toAddCommGroup := inferInstance
  mul := mul M f
  zero_mul x := by ext <;> simp
  mul_zero x := by ext <;> simp
  left_distrib x y z := by
    ext <;> simp [mul_add, TensorProduct.tmul_add, map_add, add_assoc, add_left_comm, add_comm]
  right_distrib x y z := by
    ext <;> simp [add_mul, TensorProduct.add_tmul, map_add, add_assoc, add_left_comm, add_comm]
  mul_assoc x y z := by
    apply ext
    · exact mul_assoc _ _ _
    · simp only [snd_mul, fst_mul, map_add, LinearMap.add_apply,
        M.left_assoc, M.right_assoc, M.left_right]
      have h := cocycle_equation M f hf x.fst y.fst z.fst
      linear_combination (norm := abel) h

/-- Left scalar compatibility of the cocycle multiplication. -/
abbrev scalarTower (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    IsScalarTower K (CocycleExtension M f) (CocycleExtension M f) := by
  letI := ring M f hf
  constructor
  intro r x y
  ext <;> simp [smul_mul_assoc, TensorProduct.smul_tmul, smul_add]

/-- Right scalar compatibility of the cocycle multiplication. -/
abbrev smulComm (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    SMulCommClass K (CocycleExtension M f) (CocycleExtension M f) := by
  letI := ring M f hf
  constructor
  intro r x y
  ext <;> simp [mul_smul_comm, TensorProduct.tmul_smul, smul_add]

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), extension.
Projection onto the algebra coordinate is surjective and multiplicative. -/
def extension (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    Extension K A (CocycleExtension M f) := by
  letI := ring M f hf
  letI := scalarTower M f hf
  letI := smulComm M f hf
  exact {
    sigma := {
      toFun := fun x => x.fst
      map_zero' := rfl
      map_add' := fun _ _ => rfl
      map_mul' := fun _ _ => rfl
      map_smul' := fun _ _ => rfl }
    surjective := fun a => ⟨⟨a,0⟩,rfl⟩ }

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), singularity.
Products of two vectors with zero algebra coordinate vanish. -/
theorem extension_singular (hf : IsCocycle M 2 f) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    (extension M f hf).IsSingular := by
  letI := ring M f hf
  letI := scalarTower M f hf
  letI := smulComm M f hf
  intro x y hx hy
  change x.fst = 0 at hx
  change y.fst = 0 at hy
  ext <;> simp [hx,hy]

/-- Finite-dimensional coefficients give the finite-dimensional extension
required in the section's universal segregation theorems. -/
abbrev finiteDimensional [FiniteDimensional K P] : FiniteDimensional K (CocycleExtension M f) :=
  (linearEquiv M f).symm.finiteDimensional


/-- The source's change of coordinates `(a,u) ↦ (a,u+τ(a))`. -/
def changeCoordinates (g : Cochain K A P 2) (τ : A →ₗ[K] P) :
    CocycleExtension M f ≃ₗ[K] CocycleExtension M g where
  toFun x := ⟨x.fst, x.snd + τ x.fst⟩
  invFun x := ⟨x.fst, x.snd - τ x.fst⟩
  left_inv x := by apply ext <;> simp
  right_inv x := by apply ext <;> simp
  map_add' x y := by apply ext <;> simp [map_add, add_assoc, add_left_comm, add_comm]
  map_smul' r x := by apply ext <;> simp [map_smul, smul_add]

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), cohomology invariance.
The source's explicit coordinate change is an isomorphism of extensions. -/
def coboundaryIsomorphism (g : Cochain K A P 2)
    (hf : IsCocycle M 2 f) (hg : IsCocycle M 2 g)
    (τ : A →ₗ[K] P) (hτ : f - g = delta M 1 τ) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    letI := ring M g hg
    letI := scalarTower M g hg
    letI := smulComm M g hg
    Extension.Isomorphism (extension M f hf) (extension M g hg) := by
  letI := ring M f hf
  letI := scalarTower M f hf
  letI := smulComm M f hf
  letI := ring M g hg
  letI := scalarTower M g hg
  letI := smulComm M g hg
  exact {
    toLinearEquiv := changeCoordinates M f g τ
    commutes := fun _ => rfl
    map_mul' := by
      intro x y
      apply ext
      · rfl
      · have h := LinearMap.congr_fun hτ (x.fst ⊗ₜ[K] y.fst)
        rw [delta_one_apply] at h
        change f (x.fst ⊗ₜ[K] y.fst) - g (x.fst ⊗ₜ[K] y.fst) =
          M.left x.fst (τ y.fst) - τ (x.fst*y.fst) + M.right (τ x.fst) y.fst at h
        change M.left x.fst y.snd + M.right x.snd y.fst +
          f (x.fst ⊗ₜ[K] y.fst) + τ (x.fst*y.fst) =
          M.left x.fst (y.snd + τ y.fst) +
          M.right (x.snd + τ x.fst) y.fst + g (x.fst ⊗ₜ[K] y.fst)
        simp only [map_add, LinearMap.add_apply]
        linear_combination (norm := abel) h }

/-- **Construction (unnumbered, p. 66, 2)** (Hochschild), isomorphic extensions
for two cohomologous cocycles. -/
theorem cohomologous_isomorphic (g : Cochain K A P 2)
    (hf : IsCocycle M 2 f) (hg : IsCocycle M 2 g)
    (h : IsCoboundary M 1 (f-g)) :
    letI := ring M f hf
    letI := scalarTower M f hf
    letI := smulComm M f hf
    letI := ring M g hg
    letI := scalarTower M g hg
    letI := smulComm M g hg
    Extension.Isomorphic (extension M f hf) (extension M g hg) := by
  obtain ⟨τ,hτ⟩ := h
  exact ⟨coboundaryIsomorphism M f g hf hg τ hτ⟩

end CocycleExtension
end Hochschild1945
