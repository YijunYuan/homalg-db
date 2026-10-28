import HomAlg.Hochschild1945.Def_extension
import Mathlib.Tactic.Abel

/-!
```yaml node
id: "Hochschild1945.Aux_Def_extension_section"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Auxiliary to Definition (unnumbered, p. 64)"
  pages:
    - 64
  chapter: "6"
tags:
  - "algebra-extension"
  - "technical"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_extension"
  proof: []
decls:
  - "Hochschild1945.Extension.isSegregated_iff_hasSection"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension.isSegregated_iff_hasSection:
        statement_sha256: "4813a3cb7c04dfd7fb039b01daa136fde71a670e641a90d90c0a5f0fcfa39012"
        type_hash: "0000000077ad28c6"
        meaning_hash: "466f28f02fddeb07"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
aux:
  parent: "Hochschild1945.Def_extension"
  kind: "technical"
  reason: "Verify that the source direct-sum formulation of segregation is equivalent to an algebra section,
    without assuming units."
nl_proof_source:
  follows: "agent"
```

## Statement

[Editorial] Let $\sigma:\mathfrak{B}\to\mathfrak{A}$ be a surjective homomorphism of associative, possibly nonunital algebras over $\Phi$. The extension is segregated in Hochschild's direct-sum sense if and only if there is a $\Phi$-linear multiplicative section $s:\mathfrak{A}\to\mathfrak{B}$ with $\sigma\circ s=\mathrm{id}_{\mathfrak{A}}$. No square-zero condition on the kernel is needed for this equivalence.

## Proof

For a complementary subalgebra, restrict the quotient map to it. The restriction is injective because the intersection with the kernel is zero and surjective because the two subspaces sum to the extension algebra. Its linear inverse is multiplicative since the original map is multiplicative and its restriction is injective. Thus it gives an algebra section. Conversely, a section has a subalgebra as its range. Every element b decomposes as b-s(σ(b)) plus s(σ(b)), and the intersection with the kernel is zero. The restriction is the required algebra isomorphism.

## Description

Proves that algebra sections and the source direct-sum definition of segregation agree for nonunital extensions.
-/

namespace Hochschild1945
namespace Extension

universe u

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

/-- Restrict the quotient homomorphism to a vector-space complement of its
kernel. Surjectivity and directness give a linear equivalence onto `A`. -/
noncomputable def complementEquiv (E : Extension K A B) (S : NonUnitalSubalgebra K B)
    (hS : IsCompl E.kernel S.toSubmodule) : S ≃ₗ[K] A :=
  (E.linear.kerComplementEquivRange hS.symm).trans
    (LinearEquiv.ofTop _ (LinearMap.range_eq_top.mpr E.surjective))

/-- The complementary equivalence is the original quotient map on each element. -/
@[simp] theorem complementEquiv_apply (E : Extension K A B) (S : NonUnitalSubalgebra K B)
    (hS : IsCompl E.kernel S.toSubmodule) (x : S) :
    complementEquiv E S hS x = E.sigma x := rfl

/-- **Auxiliary to Definition (unnumbered, p. 64)** (Hochschild).
The literal direct-sum definition of segregation is equivalent to an algebra
section of the original quotient map. No unit is required in either direction. -/
theorem isSegregated_iff_hasSection (E : Extension K A B) :
    E.IsSegregated ↔ E.HasSection := by
  constructor
  · rintro ⟨S, hS, _⟩
    let e := complementEquiv E S hS
    have he : ∀ x y : S, e (x * y) = e x * e y := by
      intro x y
      exact E.sigma.map_mul x y
    let s : A →ₙₐ[K] B :=
      { toFun := fun a => (e.symm a : B)
        map_zero' := by simpa using congrArg Subtype.val (map_zero e.symm)
        map_add' := fun x y => by simpa using congrArg Subtype.val (map_add e.symm x y)
        map_smul' := fun r x => by simpa using congrArg Subtype.val (map_smul e.symm r x)
        map_mul' := by
          intro x y
          have h : e.symm (x * y) = e.symm x * e.symm y := by
            apply e.injective
            rw [e.apply_symm_apply, he, e.apply_symm_apply, e.apply_symm_apply]
          exact congrArg Subtype.val h }
    refine ⟨s, ?_⟩
    intro a
    change e (e.symm a) = a
    exact e.apply_symm_apply a
  · rintro ⟨s, hs⟩
    let S := s.range
    have hS : IsCompl E.kernel S.toSubmodule := by
      constructor
      · apply Submodule.disjoint_def.mpr
        intro b hb hbs
        change ∃ a, s a = b at hbs
        obtain ⟨a, rfl⟩ := hbs
        change E.sigma (s a) = 0 at hb
        rw [hs] at hb
        simp [hb]
      · apply Submodule.codisjoint_iff_exists_add_eq.mpr
        intro b
        refine ⟨b - s (E.sigma b), s (E.sigma b), ?_, ?_, ?_⟩
        · change E.sigma (b - s (E.sigma b)) = 0
          rw [map_sub, hs, sub_self]
        · exact NonUnitalAlgHom.mem_range_self s (E.sigma b)
        · abel
    refine ⟨S, hS, complementEquiv E S hS, ?_⟩
    intro x y
    exact E.sigma.map_mul x y

end Extension
end Hochschild1945
