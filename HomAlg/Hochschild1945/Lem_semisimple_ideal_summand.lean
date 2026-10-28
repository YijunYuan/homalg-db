import HomAlg.Hochschild1945.Cited_semisimple_ideal_structure
import HomAlg.Hochschild1945.Cited_radical_structure
import HomAlg.Hochschild1945.Def_separable
import HomAlg.Hochschild1945.Def_natural_homomorphism
/-!
```yaml node
id: "Hochschild1945.Lem_semisimple_ideal_summand"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Lemma (unnumbered, p. 64)"
  pages:
    - 64
    - 65
  chapter: "6"
tags:
  - "radical"
  - "semisimple-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_separable"
    - "Hochschild1945.Def_natural_homomorphism"
  proof:
    - "Hochschild1945.Cited_radical_structure"
    - "Hochschild1945.Cited_semisimple_ideal_structure"
decls:
  - "Hochschild1945.semisimple_ideal_summand"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.semisimple_ideal_summand:
        statement_sha256: "7c2d3ab5d5b4017f1397fd1d057aeed551d95d4117b312f49ea62ee173e55b10"
        type_hash: "000000000fc7db17"
        meaning_hash: "454278340713964c"
    session: "ci-classical-section6-independent"
    author_session: "schema-taxonomy-ideal-2026-10-28"
title: "Semisimple ideals are direct summands"
```

## Statement

Now, if $\mathfrak{C}$ is any algebra and $\mathfrak{S}$ a semi-simple ideal of $\mathfrak{C}$ then $\mathfrak{C}$ is the direct sum of $\mathfrak{S}$ and another ideal $\mathfrak{T}$.

## Proof

For, if $\mathfrak{H}$ is the radical of $\mathfrak{C}$ we have $\mathfrak{S}\cap\mathfrak{H}=\{0\}$; $\mathfrak{C}/\mathfrak{H}$ is semi-simple [uses `Hochschild1945.Cited_radical_structure`] and contains the semi-simple ideal $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}\cong\mathfrak{S}$. Hence $\mathfrak{C}/\mathfrak{H}$ is the direct sum of $(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}$ and another ideal $\mathfrak{U}$. [uses `Hochschild1945.Cited_semisimple_ideal_structure`] Clearly, there exists an ideal $\mathfrak{T}\ (\supset\mathfrak{H})$ of $\mathfrak{C}$ such that $\mathfrak{U}=\mathfrak{T}/\mathfrak{H}$. Since $\mathfrak{U}\cap(\mathfrak{S}+\mathfrak{H})/\mathfrak{H}=\{0\}$ we have $\mathfrak{T}\cap\mathfrak{S}\subset\mathfrak{H}$, and since $\mathfrak{S}\cap\mathfrak{H}=\{0\}$ this implies that $\mathfrak{T}\cap\mathfrak{S}=\{0\}$. Thus, $\mathfrak{C}$ is the direct sum of $\mathfrak{S}$ and $\mathfrak{T}$.

## Description

Shows that a semisimple ideal of an algebra has a complementary ideal.

## Formalization notes

This independent argument occurs inside the proof of Proposition 6.1 and uses classical facts about the radical and semisimple quotients.

The Lean statement uses the standing finite-dimensional algebra setting; it
does not assert this conclusion for arbitrary infinite-dimensional rings.
The quotient is represented by a surjective nonunital algebra homomorphism
whose kernel is exactly the source radical. The image and inverse image ideals
are constructed from this actual homomorphism. The proof itself contains no
`sorry`; its two separately identified cited nodes retain the external results.
-/

namespace Hochschild1945

universe u

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

namespace AlgebraIdeal

/-- The image of a two-sided ideal under a surjective algebra homomorphism. -/
def mapSurjective (I : AlgebraIdeal K A) (q : A →ₙₐ[K] B)
    (hq : Function.Surjective q) : AlgebraIdeal K B where
  subalgebra := I.subalgebra.map q
  mul_mem_left := by
    intro b c hc
    obtain ⟨a, rfl⟩ := hq b
    obtain ⟨d, hd, rfl⟩ := NonUnitalSubalgebra.mem_map.mp hc
    exact NonUnitalSubalgebra.mem_map.mpr ⟨a * d, I.mul_mem_left a d hd, map_mul q a d⟩
  mul_mem_right := by
    intro b c hc
    obtain ⟨a, rfl⟩ := hq b
    obtain ⟨d, hd, rfl⟩ := NonUnitalSubalgebra.mem_map.mp hc
    exact NonUnitalSubalgebra.mem_map.mpr ⟨d * a, I.mul_mem_right a d hd, map_mul q d a⟩

/-- The inverse image of a two-sided ideal is a two-sided ideal. -/
def comap (J : AlgebraIdeal K B) (q : A →ₙₐ[K] B) : AlgebraIdeal K A where
  subalgebra := J.subalgebra.comap q
  mul_mem_left := by
    intro a b hb
    change q (a * b) ∈ J.subalgebra
    rw [map_mul]
    exact J.mul_mem_left (q a) (q b) hb
  mul_mem_right := by
    intro a b hb
    change q (b * a) ∈ J.subalgebra
    rw [map_mul]
    exact J.mul_mem_right (q a) (q b) hb

end AlgebraIdeal

attribute [local instance] idealFiniteDimensional

/-- **Lemma (unnumbered, p. 64)** (Hochschild). A semisimple ideal of a
finite-dimensional associative algebra has an ideal complement, even when the
ambient algebra is not semisimple and neither algebra is assumed unital.

Proof: take the actual radical quotient, complement the image ideal in that
semisimple quotient, and pull the complement back. The intersection is zero
because the original ideal meets the radical in zero. Surjectivity and the
quotient decomposition show that the two original subspaces span the algebra.
The only classical external boundaries are the two cited source nodes. -/
theorem semisimple_ideal_summand [FiniteDimensional K A] (I : AlgebraIdeal K A)
    (hI : Semisimple K I.subalgebra) :
    ∃ J : AlgebraIdeal K A, IsCompl I.subalgebra.toSubmodule J.subalgebra.toSubmodule := by
  obtain ⟨Q⟩ := cited_radical_quotient K A
  let := Q.ring
  let := Q.module
  let := Q.comm
  let := Q.tower
  let := Q.finite
  let imageIdeal := I.mapSurjective Q.quotient Q.surjective
  obtain ⟨_, J, hJ⟩ := cited_semisimple_ideal_structure K Q.carrier Q.semisimple imageIdeal
  refine ⟨J.comap Q.quotient, ?_⟩
  constructor
  · apply Submodule.disjoint_def.mpr
    intro a ha hb
    have hqa : Q.quotient a = 0 := Submodule.disjoint_def.mp hJ.disjoint
      (Q.quotient a) (NonUnitalSubalgebra.mem_map.mpr ⟨a, ha, rfl⟩) hb
    exact cited_semisimple_inter_radical K A I hI a ha ((Q.kernel a).mp hqa)
  · apply Submodule.codisjoint_iff_exists_add_eq.mpr
    intro a
    obtain ⟨b, c, hb, hc, hbc⟩ :=
      Submodule.codisjoint_iff_exists_add_eq.mp hJ.codisjoint (Q.quotient a)
    obtain ⟨s, hs, hqs⟩ := NonUnitalSubalgebra.mem_map.mp hb
    refine ⟨s, a - s, hs, ?_, by abel⟩
    change Q.quotient (a - s) ∈ J.subalgebra
    rw [map_sub, hqs, ← hbc]
    simpa using hc

end Hochschild1945
