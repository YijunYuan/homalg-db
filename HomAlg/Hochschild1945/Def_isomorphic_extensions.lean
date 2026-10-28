import HomAlg.Hochschild1945.Def_extension

/-!
```yaml node
id: "Hochschild1945.Def_isomorphic_extensions"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 65)"
  pages:
    - 65
  chapter: "6"
tags:
  - "algebra-extension"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_extension"
  proof: []
decls:
  - "Hochschild1945.Extension.Isomorphism"
  - "Hochschild1945.Extension.Isomorphic"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension.Isomorphism:
        statement_sha256: "c756ea9188bdd13b016bcb2ff6f6660d1e349730d09187e7f46124576077cd77"
        type_hash: "0000000066f0b137"
        meaning_hash: "9eddd01b691bf3fe"
      Hochschild1945.Extension.Isomorphic:
        statement_sha256: "1bc660b8367b1c2323e5a4771dd3ab6924c72302d670d34a1a4fb20938f4d258"
        type_hash: "000000008ebf0f01"
        meaning_hash: "9436b160c9104100"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Isomorphic extensions"
```

## Statement

We shall say that two extensions $\{\mathfrak{B},\sigma\}$ and $\{\mathfrak{B}^*,\sigma^*\}$ are isomorphic if there exists an isomorphism $I$ of $\mathfrak{B}$ onto $\mathfrak{B}^*$ such that $\sigma^*I=\sigma$.

## Description

Defines an isomorphism of extensions as an algebra isomorphism commuting with the quotient maps.
-/

namespace Hochschild1945

universe u

namespace Extension

variable {K A B C : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]
  [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]

/-- **Definition (unnumbered, p. 65)** (Hochschild). A linear multiplicative
isomorphism of the extension algebras that commutes with their quotient maps. -/
structure Isomorphism (E : Extension K A B) (F : Extension K A C) extends B ≃ₗ[K] C where
  /-- The algebra isomorphism preserves multiplication. -/
  map_mul' : ∀ x y : B, toLinearEquiv (x * y) = toLinearEquiv x * toLinearEquiv y
  /-- The displayed identity `σ* I = σ` in the source. -/
  commutes : ∀ x : B, F.sigma (toLinearEquiv x) = E.sigma x

/-- **Definition (unnumbered, p. 65) (existence)** (Hochschild). The two source
extensions are isomorphic exactly when such a commuting algebra isomorphism exists. -/
def Isomorphic (E : Extension K A B) (F : Extension K A C) : Prop :=
  Nonempty (Isomorphism E F)

/-- The identity algebra map is an isomorphism of an extension with itself. -/
def Isomorphism.refl (E : Extension K A B) : Isomorphism E E where
  toLinearEquiv := LinearEquiv.refl K B
  map_mul' := fun _ _ => rfl
  commutes := fun _ => rfl

/-- The inverse algebra map again commutes with the extension homomorphisms. -/
def Isomorphism.symm {E : Extension K A B} {F : Extension K A C}
    (I : Isomorphism E F) : Isomorphism F E where
  toLinearEquiv := I.toLinearEquiv.symm
  map_mul' := by
    intro x y
    apply I.toLinearEquiv.injective
    simp [I.map_mul']
  commutes := by
    intro x
    simpa using (I.commutes (I.toLinearEquiv.symm x)).symm

end Extension
end Hochschild1945
