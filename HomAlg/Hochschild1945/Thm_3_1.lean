import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import HomAlg.Hochschild1945.Def_2_2
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Con_bar_map
import HomAlg.Hochschild1945.Def_2_1
import HomAlg.Hochschild1945.Prop_1_1

/-!
```yaml node
id: "Hochschild1945.Thm_3_1"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Theorem 3.1"
  pages:
    - 60
  chapter: "3"
tags:
  - "cochain-complex"
  - "cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_2_2"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
    - "Hochschild1945.Prop_1_1"
  proof:
    - "Hochschild1945.Con_bar_map"
    - "Hochschild1945.Def_2_1"
decls:
  - "Hochschild1945.fundamental_isomorphism"
  - "Hochschild1945.dimensionShift"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.fundamental_isomorphism:
        statement_sha256: "826f9663c760e0969c2d0c3e56fe1746742f7e1c419fa575d3e2010f0140569a"
        type_hash: "00000000764ed476"
        meaning_hash: "1eed93a4b1abd4e6"
      Hochschild1945.dimensionShift:
        statement_sha256: "0794ece018b4b6358d16543aa73ef94963a2cef48561853fa0bcc7f9cedc6850"
        type_hash: "00000000fa1ccd7d"
        meaning_hash: "ed1e5fcad65480d5"
    session: "root-sections123-independent"
    author_session: "/root/lean_fixtures"
title: "Fundamental dimension-shift isomorphism"
```

## Statement

If $m\geqq 2$, $H^m(\mathfrak{A},\mathfrak{P})\cong H^{m-1}(\mathfrak{A},(\mathfrak{A}:\mathfrak{P}))$.

## Proof

It is obvious that the mapping $f\to\bar f$, defined in section 2, maps
$(\mathfrak{A}^{(m)}:\mathfrak{P})$ isomorphically onto $(\mathfrak{A}^{(m-1)}:(\mathfrak{A}:\mathfrak{P}))$, for
$m\geqq 1$. The relation $\overline{\delta f}=\delta\bar f$ shows furthermore
that this isomorphism maps the group of $(m,\mathfrak{P})$-cocycles onto the group of
$(m-1,(\mathfrak{A}:\mathfrak{P}))$-cocycles. Finally, if $\dim(f)\geqq 2$,
$\bar f=\delta g$ if and only if $f=\delta g$. Hence the mapping $f\to\bar f$
induces an isomorphism between $H^m(\mathfrak{A},\mathfrak{P})$ and $H^{m-1}(\mathfrak{A},(\mathfrak{A}:\mathfrak{P}))$:

[uses `Hochschild1945.Con_bar_map`] [uses `Hochschild1945.Def_2_1`]

## Description

The source bar map induces an actual linear isomorphism on the quotient cohomology groups in every degree at least two.
## Formalization notes

The source reuses the letter `g` for primitives in the two cochain spaces.
`bar_mem_coboundaries` makes the change of carrier explicit by currying or
uncurrying the primitive. The printed text is retained; the resulting quotient
isomorphism is constructed, not supplied as a hypothesis.
-/

namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- The source bar map restricts to an equivalence on cocycles, because it commutes
with the coboundary and is injective in the next degree. -/
def barCocycles (n : Nat) : cocycles M (n + 1) ≃ₗ[K] cocycles (twistedModule M) n where
  toFun f := ⟨barEquiv K A P n f, by
    change delta (twistedModule M) n (barEquiv K A P n f) = 0
    rw [← bar_delta, show delta M (n + 1) f = 0 from f.property, map_zero]⟩
  invFun g := ⟨(barEquiv K A P n).symm g, by
    change delta M (n + 1) ((barEquiv K A P n).symm g) = 0
    apply (barEquiv K A P (n + 1)).injective
    rw [bar_delta, LinearEquiv.apply_symm_apply, map_zero]
    exact g.property⟩
  left_inv f := Subtype.ext ((barEquiv K A P n).symm_apply_apply f)
  right_inv g := Subtype.ext ((barEquiv K A P n).apply_symm_apply g)
  map_add' f g := Subtype.ext ((barEquiv K A P n).map_add f g)
  map_smul' c f := Subtype.ext ((barEquiv K A P n).map_smul c f)

/-- The cocycle restriction retains the original bar map on underlying cochains. -/
@[simp] theorem barCocycles_apply (n : Nat) (f : cocycles M (n + 1)) :
    (barCocycles M n f : Cochain K A (A →ₗ[K] P) n) = barEquiv K A P n f := rfl

/-- In degrees at least two, currying preserves and reflects coboundaries.
A primitive in the shifted module is uncurried to obtain the primitive in the original module. -/
theorem bar_mem_coboundaries (n : Nat) (f : Cochain K A P (n + 2)) :
    barEquiv K A P (n + 1) f ∈ coboundaries (twistedModule M) (n + 1) ↔
      f ∈ coboundaries M (n + 2) := by
  constructor
  · rintro ⟨g, hg⟩
    refine ⟨(barEquiv K A P n).symm g, ?_⟩
    apply (barEquiv K A P (n + 1)).injective
    rw [bar_delta, LinearEquiv.apply_symm_apply]
    exact hg
  · rintro ⟨g, rfl⟩
    exact ⟨barEquiv K A P n g, (bar_delta M n g).symm⟩

/-- The restricted bar equivalence maps the boundary subgroup onto the shifted
boundary subgroup, the final premise required to descend to the quotient. -/
theorem bar_boundaries_map (n : Nat) :
    (boundariesInCycles M (n + 2)).map (barCocycles M (n + 1)).toLinearMap =
      boundariesInCycles (twistedModule M) (n + 1) := by
  ext g
  simp only [Submodule.mem_map]
  constructor
  · rintro ⟨f, hf, rfl⟩
    exact (mem_boundariesInCycles (twistedModule M) (n + 1) _).mpr
      ((bar_mem_coboundaries M n f).mpr ((mem_boundariesInCycles M (n + 2) f).mp hf))
  · intro hg
    refine ⟨(barCocycles M (n + 1)).symm g, ?_,
      (barCocycles M (n + 1)).apply_symm_apply g⟩
    apply (mem_boundariesInCycles M (n + 2) _).mpr
    apply (bar_mem_coboundaries M n _).mp
    change barEquiv K A P (n + 1) ((barEquiv K A P (n + 1)).symm g) ∈ _
    rw [LinearEquiv.apply_symm_apply]
    exact (mem_boundariesInCycles (twistedModule M) (n + 1) g).mp hg

/-- **Theorem 3.1**. The actual isomorphism induced by the source bar map on the
quotient of cocycles by coboundaries, in every degree `n + 2`. -/
def dimensionShift (n : Nat) :
    Cohomology M (n + 2) ≃ₗ[K] Cohomology (twistedModule M) (n + 1) :=
  Submodule.Quotient.equiv (boundariesInCycles M (n + 2))
    (boundariesInCycles (twistedModule M) (n + 1))
    (barCocycles M (n + 1)) (bar_boundaries_map M n)

/-- **Theorem 3.1** in the printed indexing: if `m ≥ 2`, then
`H^m(A,P)` is isomorphic to `H^(m-1)(A,(A:P))`. Its witness is the quotient map above. -/
theorem fundamental_isomorphism (m : Nat) (hm : 2 ≤ m) :
    Nonempty (Cohomology M m ≃ₗ[K] Cohomology (twistedModule M) (m - 1)) := by
  cases m with
  | zero => contradiction
  | succ m =>
      cases m with
      | zero => contradiction
      | succ n => exact ⟨dimensionShift M n⟩

end Hochschild1945
