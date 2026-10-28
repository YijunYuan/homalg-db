import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Con_extension_module
import HomAlg.Hochschild1945.Aux_Def_extension_section
import HomAlg.Hochschild1945.Con_extension_cocycle
import HomAlg.Hochschild1945.Con_cocycle_extension
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_extension
import HomAlg.Hochschild1945.Prop_6_2

/-!
```yaml node
id: "Hochschild1945.Prop_6_3"
doc: "Hochschild1945"
kind: "proposition"
source:
  label: "Proposition 6.3"
  pages:
    - 67
  chapter: "6"
tags:
  - "hochschild-cohomology"
  - "segregated-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Con_extension_module"
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_extension"
  proof:
    - "Hochschild1945.Aux_Def_extension_section"
    - "Hochschild1945.Con_cocycle_extension"
    - "Hochschild1945.Con_extension_cocycle"
    - "Hochschild1945.Def_2_1"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Prop_6_2"
decls:
  - "Hochschild1945.Extension.isSegregated_iff_sectionClass_zero"
fidelity:
  status: "deviates"
  deviations:
    - kind: "proof-route"
      what: "The Lean proof corrects the linear section directly by subtracting a primitive of its defect,
        instead of invoking the full classification and transporting segregation from the zero-cocycle
        extension."
      why: "The explicit calculation proves the same zero-class criterion while exposing the underlying
        multiplication identities. The original classification route and its dependencies remain preserved
        as source evidence."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension.isSegregated_iff_sectionClass_zero:
        statement_sha256: "f0685b0086e75b1a9012ccbe4fd52b32692c677228ae316c8a709648782b9865"
        type_hash: "00000000508207f7"
        meaning_hash: "205ec35addcfc15f"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Segregation and the zero cohomology class"
```

## Statement

$\mathfrak{A}$ is segregated in a singular extension if and only if the corresponding cohomology class is zero.

## Proof

We note that if $\mathfrak{A}$ is segregated in the extension $\{\mathfrak{B}^*,\sigma^*\}$, and if $\{\mathfrak{B},\sigma\}$ is isomorphic with $\{\mathfrak{B}^*,\sigma^*\}$, then $\mathfrak{A}$ is segregated also in $\{\mathfrak{B},\sigma\}$. Now let $\{\mathfrak{B},\sigma\}$ be an extension which determines a zero cohomology class. Then it is obvious that $\mathfrak{A}$ is segregated in the extension $\{\mathfrak{B}_0,\sigma^*\}$ constructed from the representative $f=0$ of this class. [uses `Hochschild1945.Con_cocycle_extension`] Since $\{\mathfrak{B},\sigma\}$ is isomorphic with $\{\mathfrak{B}_0,\sigma^*\}$, $\mathfrak{A}$ is segregated in $\{\mathfrak{B},\sigma\}$. The necessity of the condition is obvious. [uses `Hochschild1945.Prop_6_2`]

[uses `Hochschild1945.Aux_Def_extension_section`] [uses `Hochschild1945.Con_extension_cocycle`] [uses `Hochschild1945.Def_2_1`] [uses `Hochschild1945.Def_two_sided_module`]

## Description

Characterizes segregation of a singular extension by vanishing of its associated cohomology class.
## Formalization notes

The class is an element of the actual quotient defined in Definition 2.3.
The Lean proof expands the source's zero-class coordinate change directly:
if the section defect is δg, subtract g from the section to obtain a
multiplicative section. This is the explicit calculation underlying the
isomorphism with the zero-cocycle extension in the source proof. Conversely,
an algebra section has zero defect, and section independence gives a boundary.
The algebra-section/direct-sum equivalence is proved in the auxiliary node.
[uses `Hochschild1945.Aux_Def_extension_section`]
[uses `Hochschild1945.Con_extension_cocycle`]

This is an explicit proof-route deviation: the printed proof passes through
Proposition 6.2, the zero-cocycle extension, and preservation of segregation under
extension isomorphism. The formal proof uses the direct section correction
instead. `Hochschild1945.Prop_6_2` and `Hochschild1945.Con_cocycle_extension` remain
in the authored source proof dependencies and imports. Their appearance in the
generated `deps_diff.declared_not_verified.proof` records this deliberate route difference;
it is not evidence that their formal declarations were used.


The separate `mathlib-bypass-proof` warning matches NonUnitalAlgHom, the type
of the explicitly constructed corrected algebra section. Its multiplication
law is proved by expanding the source coboundary equation and the square-zero
kernel law; no Mathlib extension-splitting or Hochschild theorem is invoked.
The source two-sided-module definition remains in use. This datatype match is
distinct from the already recorded proof-route deviation above, whose source-only
Proposition 6.2 and cocycle-extension edges remain visible.

-/

namespace Hochschild1945
namespace Extension

universe u
open scoped TensorProduct

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

/-- Correcting a linear section by a primitive of its defect gives an algebra section. -/
def correctedSection (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (g : A →ₗ[K] E.kernel)
    (hg : sectionCocycle E ρ hρ = delta (E.kernelModule hE ρ hρ) 1 g) :
    A →ₙₐ[K] B where
  __ := ρ - E.kernel.subtype.comp g
  map_zero' := by simp
  map_mul' a b := by
    have h := LinearMap.congr_fun hg (a ⊗ₜ[K] b)
    rw [delta_one_apply] at h
    have hv := congrArg (fun x : E.kernel => (x : B)) h
    change ρ a * ρ b - ρ (a*b) =
      ρ a * (g b : B) - (g (a*b) : B) + (g a : B) * ρ b at hv
    have hz : (g a : B) * (g b : B) = 0 := hE _ _ (g a).property (g b).property
    change ρ (a*b) - (g (a*b) : B) =
      (ρ a - (g a : B)) * (ρ b - (g b : B))
    simp only [sub_mul, mul_sub, hz, sub_zero]
    linear_combination (norm := abel) -hv

/-- Correcting by a kernel-valued map preserves the section equation. -/
theorem correctedSection_section (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a)
    (g : A →ₗ[K] E.kernel)
    (hg : sectionCocycle E ρ hρ = delta (E.kernelModule hE ρ hρ) 1 g) (a : A) :
    E.sigma (correctedSection E hE ρ hρ g hg a) = a := by
  change E.sigma (ρ a - (g a : B)) = a
  rw [map_sub, hρ, show E.sigma (g a : B) = 0 from (g a).property, sub_zero]

/-- The explicit primitive form of Proposition 6.3. -/
theorem isSegregated_iff_sectionCocycle_coboundary (E : Extension K A B)
    (hE : E.IsSingular) (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    E.IsSegregated ↔ IsCoboundary (E.kernelModule hE ρ hρ) 1 (sectionCocycle E ρ hρ) := by
  rw [isSegregated_iff_hasSection]
  constructor
  · rintro ⟨s,hs⟩
    let τ : A →ₗ[K] B := LinearMap.ofClass s
    have hτ : ∀ a, E.sigma (τ a) = a := hs
    have hz : sectionCocycle E τ hτ = 0 := by
      apply TensorProduct.ext'
      intro a b
      apply Subtype.ext
      change s a * s b - s (a*b) = 0
      rw [map_mul, sub_self]
    have h := sectionCocycle_cohomologous E hE ρ τ hρ hτ
    simpa only [hz, sub_zero] using h
  · rintro ⟨g,hg⟩
    exact ⟨correctedSection E hE ρ hρ g hg, correctedSection_section E hE ρ hρ g hg⟩

/-- The cohomology class actually determined by a section of a singular extension. -/
def sectionClass (E : Extension K A B) (hE : E.IsSingular)
    (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    Cohomology (E.kernelModule hE ρ hρ) 2 :=
  Submodule.Quotient.mk ⟨sectionCocycle E ρ hρ, sectionCocycle_isCocycle E hE ρ hρ⟩

/-- **Proposition 6.3** (Hochschild). A singular extension is segregated exactly
when its corresponding class in the actual degree-two quotient is zero. -/
theorem isSegregated_iff_sectionClass_zero (E : Extension K A B)
    (hE : E.IsSingular) (ρ : A →ₗ[K] B) (hρ : ∀ a, E.sigma (ρ a) = a) :
    E.IsSegregated ↔ sectionClass E hE ρ hρ = 0 := by
  rw [isSegregated_iff_sectionCocycle_coboundary E hE ρ hρ]
  change IsCoboundary (E.kernelModule hE ρ hρ) 1 (sectionCocycle E ρ hρ) ↔
    (Submodule.Quotient.mk ⟨sectionCocycle E ρ hρ, sectionCocycle_isCocycle E hE ρ hρ⟩ :
      cocycles (E.kernelModule hE ρ hρ) 2 ⧸ boundariesInCycles (E.kernelModule hE ρ hρ) 2) = 0
  rw [Submodule.Quotient.mk_eq_zero, mem_boundariesInCycles, mem_coboundaries]

end Extension
end Hochschild1945
