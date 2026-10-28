import Mathlib.FieldTheory.PurelyInseparable.Basic
import Mathlib.FieldTheory.IntermediateField.Adjoin.Algebra
import Mathlib.FieldTheory.IntermediateField.Adjoin.Basic
import Mathlib.Order.Minimal
import Mathlib.Algebra.Polynomial.Derivation
import Mathlib.FieldTheory.Minpoly.Field

import HomAlg.Hochschild1945.Def_2_2

/-!
```yaml node
id: "Hochschild1945.Lem_4_1"
doc: "Hochschild1945"
kind: "lemma"
source:
  label: "Lemma 4.1"
  pages:
    - 62
    - 63
  chapter: "4"
tags:
  - "derivation"
  - "separable-algebra"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_2"
  proof: []
decls:
  - "Hochschild1945.inseparable_field_derivation"
fidelity:
  status: "deviates"
  deviations:
    - kind: "generality"
      what: "Restrict the printed algebraic field-extension statement to finite-dimensional extensions
        L/K."
      why: "The article applies the lemma to a finite-dimensional center, and its construction requires
        an intermediate field with a final degree-p purely inseparable step. The unrestricted infinite
        algebraic-extension reading fails for the perfect closure of F_p(t), where every element is a
        pth power and every derivation vanishes."
    - kind: "proof-route"
      what: "Choose a maximal proper intermediate field and descend polynomial differentiation using the
        vanishing derivative of the generator's minimal polynomial."
      why: "This retains the source's intermediate-field and differentiated-powers construction, with
        generator derivative one. The formal proof verifies the equivalent descent condition directly,
        rather than separately proving the displayed degree-p step or c^p membership."
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.inseparable_field_derivation:
        statement_sha256: "ebd0c7eadd39e397fef8016c1257332e592da423dd158d668f62ee0aec270518"
        type_hash: "0000000027cf95b2"
        meaning_hash: "0000000027cf95b2"
    session: "root-section4-and-quotient-independent"
    author_session: "/root/ci_governance"
title: "Nonzero derivations of inseparable fields"
```

## Statement

Let $\Phi$ be a field of characteristic $p$ $(\ne 0)$, $\mathfrak{C}$ an inseparable
algebraic extension of $\Phi$. Then there exists a non-zero derivation of
$\mathfrak{C}$ (i.e. a non-cobounding $(1,\mathfrak{C})$-cocycle of $\mathfrak{C}$) over $\Phi$.

## Proof

It is easy to see that there exists an intermediate field $\mathfrak{S}$ over $\Phi$ such that $\mathfrak{C}=\mathfrak{S}(c)$, where $c^p\in\mathfrak{S}$. We define a linear mapping $D$ of $\mathfrak{C}$ into itself by setting $D\{s\}=0$, for every $s\in\mathfrak{S}$, and $D(sc^q)=sqc^{q-1}c_0$, where $c_0$ is an arbitrary fixed element $(\ne 0)$ of $\mathfrak{C}$. It is easy to verify that $D$ is a non-zero derivation of $\mathfrak{C}$ over $\mathfrak{S}$, and hence also over $\Phi$.

## Description

Produces a nonzero derivation of an inseparable algebraic extension in positive characteristic.

## Formalization notes

The formal statement explicitly restricts the printed algebraic extension to finite-dimensional L/K. The article's application is to the finite-dimensional center of a simple algebra, and the displayed construction chooses an intermediate field S and a final degree-p generator. The finite restriction is recorded as a generality deviation; it is not an assertion that the lemma's printed wording explicitly includes finiteness or a claim about the author's unstated intention.

The unrestricted infinite reading fails for the perfect closure of F_p(t): this is an inseparable algebraic extension, but every element is a pth power, so the Leibniz rule in characteristic p forces every derivation to vanish. The original Statement remains unchanged. No new source-error adjudication is asserted by this scope choice.

The source parenthetical description in terms of non-cobounding one-cocycles explains the declared source dependency on Hochschild1945.Def_2_2. The formal statement spells out the nonzero linear map and Leibniz identity directly, so this source-level dependency is not a compiled statement dependency.

The complete local proof chooses a maximal proper intermediate field containing
the separable closure by minimizing the remaining finite extension degree. Any
generator outside that field generates the whole extension, and its irreducible
minimal polynomial has derivative zero because the final extension is purely
inseparable. Polynomial differentiation preserves the evaluation kernel, so it
descends to a derivation sending the generator to one. Restricting scalars gives
the required ground-field derivation. This follows the source's construction,
but uses the derivative-zero descent criterion instead of separately establishing
the displayed relation c^p in S or asserting that the final degree is p. This
difference is recorded as a proof-route deviation. There is no local `sorry`
or classical cited assumption in this proof.

Accordingly, the retained `deps_diff.declared_not_verified.statement` entry
for Def_2_2 records the printed parenthetical cocycle interpretation. The
compiled main type states nonzero linearity and the Leibniz identity directly;
no artificial invocation of a cochain definition is added merely to empty the
source-to-compiled dependency difference.

-/

namespace Hochschild1945.Lemma41Support

open Polynomial IntermediateField
universe u

/-- In a finite inseparable extension, a proper intermediate field containing
the separable closure can be chosen maximal. Minimize the positive degree of
the remaining extension; strict inclusion strictly decreases that degree. -/
theorem maximal_proper_above_separable_closure (K L : Type u)
    [Field K] [Field L] [Algebra K L] [FiniteDimensional K L]
    (h : ¬ Algebra.IsSeparable K L) :
    ∃ S : IntermediateField K L, separableClosure K L ≤ S ∧ S ≠ ⊤ ∧
      ∀ T : IntermediateField K L, S < T → T = ⊤ := by
  classical
  have hsep : separableClosure K L ≠ ⊤ := fun he => h ((separableClosure.eq_top_iff K L).mp he)
  obtain ⟨S, hS⟩ := exists_minimalFor_of_wellFoundedLT
    (fun S : IntermediateField K L => separableClosure K L ≤ S ∧ S ≠ ⊤)
    (fun S => Module.finrank S L) ⟨separableClosure K L, le_rfl, hsep⟩
  refine ⟨S, hS.1.1, hS.1.2, ?_⟩
  intro T hST
  by_contra hT
  have hlt : Module.finrank T L < Module.finrank S L := IntermediateField.finrank_lt_of_gt hST
  exact (not_le_of_gt hlt) (hS.le_of_le ⟨hS.1.1.trans hST.le, hT⟩ hlt.le)

/-- The final simple step of a finite inseparable extension has a generator
whose minimal polynomial has derivative zero. Its polynomial evaluation is
surjective, so formal differentiation can descend to the extension field. -/
theorem inseparable_final_generator (K L : Type u)
    [Field K] [Field L] [Algebra K L] [FiniteDimensional K L]
    (h : ¬ Algebra.IsSeparable K L) :
    ∃ (S : IntermediateField K L) (c : L), c ∉ S ∧
      Function.Surjective (Polynomial.aeval c : S[X] →ₐ[S] L) ∧
      Polynomial.derivative (minpoly S c) = 0 := by
  classical
  obtain ⟨S, hsep, hS, hmax⟩ := maximal_proper_above_separable_closure K L h
  obtain ⟨c, hc⟩ : ∃ c : L, c ∉ S := by
    by_contra! hmem
    apply hS
    exact top_unique (fun x _ => hmem x)
  have hlt : S < S ⊔ IntermediateField.adjoin K {c} := by
    apply lt_of_le_of_ne le_sup_left
    intro he
    apply hc
    rw [he]
    have hle : IntermediateField.adjoin K {c} ≤ S ⊔ IntermediateField.adjoin K {c} := le_sup_right
    exact hle (IntermediateField.mem_adjoin_simple_self K c)
  have htop := hmax _ hlt
  have hgen : IntermediateField.adjoin S {c} = ⊤ := by
    apply IntermediateField.restrictScalars_injective K
    rw [IntermediateField.restrictScalars_adjoin_eq_sup, IntermediateField.restrictScalars_top]
    exact htop
  have halg : Algebra.adjoin S ({c} : Set L) = ⊤ :=
    (IntermediateField.adjoin_eq_top_iff).mp hgen
  have hsurj : Function.Surjective (Polynomial.aeval c : S[X] →ₐ[S] L) := by
    intro x
    have hx : x ∈ Algebra.adjoin S ({c} : Set L) := by rw [halg]; trivial
    rw [Algebra.adjoin_singleton_eq_range_aeval] at hx
    exact hx
  let : IsPurelyInseparable S L := (separableClosure_le_iff K L S).mp hsep
  have hnsep : ¬ IsSeparable S c := by
    intro hs
    obtain ⟨s, hs⟩ := IsPurelyInseparable.inseparable S c hs
    apply hc
    rw [← hs]
    exact s.property
  refine ⟨S, c, hc, hsurj, ?_⟩
  by_contra hd
  apply hnsep
  exact (Polynomial.separable_iff_derivative_ne_zero
    (minpoly.irreducible (Algebra.IsIntegral.isIntegral c))).mpr hd

end Hochschild1945.Lemma41Support

namespace Hochschild1945.Lemma41Support

open Polynomial

universe u

/-- Polynomial differentiation descends through a simple extension when the
minimal polynomial has derivative zero. It sends the generator to one, so the
result is nonzero. This is precisely the differentiation step in Lemma 4.1. -/
theorem simple_extension_derivation (S L : Type u) [Field S] [Field L] [Algebra S L]
    (c : L) (hgen : Function.Surjective (Polynomial.aeval c : S[X] →ₐ[S] L))
    (hmin : Polynomial.derivative (minpoly S c) = 0) :
    ∃ D : L →ₗ[S] L, D c = 1 ∧ D ≠ 0 ∧
      ∀ x y : L, D (x * y) = x * D y + D x * y := by
  have hstable : ∀ f : S[X], Polynomial.aeval c f = 0 →
      Polynomial.aeval c (Polynomial.derivative' f) = 0 := by
    intro f hf
    obtain ⟨g, rfl⟩ := minpoly.dvd S c hf
    change Polynomial.aeval c (Polynomial.derivative (minpoly S c * g)) = 0
    rw [Polynomial.derivative_mul, hmin, zero_mul, zero_add, map_mul, minpoly.aeval, zero_mul]
  let D : Derivation S L L := Derivation.liftOfSurjective hgen hstable
  have hc : D c = 1 := by
    have h := Derivation.liftOfSurjective_apply hgen hstable (Polynomial.X : S[X])
    simpa [Polynomial.derivative', D] using h
  refine ⟨D.toLinearMap, hc, ?_, ?_⟩
  · intro hz
    have h := congrArg (fun f : L →ₗ[S] L => f c) hz
    change D c = 0 at h
    rw [hc] at h
    exact one_ne_zero h
  · intro x y
    simpa [mul_comm] using D.leibniz x y

end Hochschild1945.Lemma41Support


namespace Hochschild1945
universe u

/-- **Lemma 4.1** (Hochschild). A finite inseparable extension in positive
characteristic has a nonzero derivation over the ground field. Choose a maximal
proper intermediate field and descend polynomial differentiation through the
minimal polynomial, whose derivative vanishes. -/
theorem inseparable_field_derivation (K L : Type u) [Field K] [Field L]
    [Algebra K L] [FiniteDimensional K L] (p : ℕ) [Fact p.Prime] [CharP K p]
    (h : ¬ Algebra.IsSeparable K L) :
    ∃ D : L →ₗ[K] L, D ≠ 0 ∧ ∀ x y : L, D (x * y) = x * D y + D x * y := by
  obtain ⟨S, c, _, hgen, hmin⟩ := Lemma41Support.inseparable_final_generator K L h
  obtain ⟨D, _, hD, hLeibniz⟩ := Lemma41Support.simple_extension_derivation S L c hgen hmin
  refine ⟨D.restrictScalars K, ?_, hLeibniz⟩
  intro hz
  apply hD
  apply LinearMap.ext
  intro x
  exact congrArg (fun f : L →ₗ[K] L => f x) hz

end Hochschild1945
