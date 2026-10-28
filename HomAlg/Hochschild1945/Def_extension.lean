import Mathlib.Algebra.Algebra.NonUnitalSubalgebra
import Mathlib.LinearAlgebra.FiniteDimensional.Defs
import Mathlib.LinearAlgebra.Prod

/-!
```yaml node
id: "Hochschild1945.Def_extension"
doc: "Hochschild1945"
kind: "definition"
source:
  label: "Definition (unnumbered, p. 64)"
  pages:
    - 64
  chapter: "6"
tags:
  - "algebra-extension"
  - "segregated-extension"
  - "singular-extension"
concepts:
  defines: []
  uses: []
deps:
  statement: []
  proof: []
decls:
  - "Hochschild1945.Extension"
  - "Hochschild1945.Extension.IsSingular"
  - "Hochschild1945.Extension.IsSegregated"
fidelity:
  status: "faithful"
  reviewed:
    by: "codex-root"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.Extension:
        statement_sha256: "1de9834d880adf4c9685d31667e3bafe5d990a68e137734e027d6d71ae8de8b9"
        type_hash: "00000000e798c7ad"
        meaning_hash: "00000000e798c7ad"
      Hochschild1945.Extension.IsSingular:
        statement_sha256: "5785e09c7eb9b0bf130ff03477024348475a60d692cf0e21e01868456750e207"
        type_hash: "00000000a9f80be5"
        meaning_hash: "7e7be083acbf83bc"
      Hochschild1945.Extension.IsSegregated:
        statement_sha256: "748a3d698ffb90f72cf93500b318f10c5fc7bf65a9d43bb421a2d584e09a9efc"
        type_hash: "00000000a9f80be5"
        meaning_hash: "7e7be083acbf83bc"
    session: "root-section6-independent"
    author_session: "/root/ci_governance"
title: "Extensions, singularity, and segregation"
```

## Statement

Let $\mathfrak{A}$ be an algebra over $\Phi$. By an extension of $\mathfrak{A}$ we shall mean a pair $\{\mathfrak{B},\sigma\}$, where $\mathfrak{B}$ is an algebra over $\Phi$ and $\sigma$ a homomorphism of $\mathfrak{B}$ onto $\mathfrak{A}$. The extension $\{\mathfrak{B},\sigma\}$ is called singular if the kernel $\mathfrak{K}$ of $\sigma$ satisfies the condition $\mathfrak{K}^2=\{0\}$. $\mathfrak{A}$ is said to be segregated in the extension $\{\mathfrak{B},\sigma\}$ if $\mathfrak{B}$ is the direct sum of $\mathfrak{K}$ and a subalgebra $\mathfrak{A}^*$ isomorphic with $\mathfrak{A}$.

## Description

Defines algebra extensions, singular extensions and segregation by a complementary subalgebra.
## Formalization notes

The extension carrier B is not assumed finite-dimensional: the source cocycle
construction applies to A ⊕ P with arbitrary coefficient space P. The universal
segregation claims later in section 6 explicitly quantify finite-dimensional B;
that theorem scope is kept separate from this general definition.

-/

namespace Hochschild1945

universe u

/-- **Definition (unnumbered, p. 64)** (Hochschild). An extension is the source's
surjective algebra homomorphism onto `A`. Neither algebra is assumed unital. -/
structure Extension (K A B : Type u) [Field K]
    [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
    [FiniteDimensional K A]
    [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B] where
  /-- The homomorphism in the pair `{B, σ}`. -/
  sigma : B →ₙₐ[K] A
  /-- The source requires that `σ` maps onto `A`. -/
  surjective : Function.Surjective sigma

namespace Extension

variable {K A B : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing B] [Module K B] [SMulCommClass K B B] [IsScalarTower K B B]

/-- The linear map underlying the source's quotient homomorphism. -/
abbrev linear (E : Extension K A B) : B →ₗ[K] A := LinearMap.ofClass E.sigma

/-- The kernel in the source, represented as a vector subspace. -/
abbrev kernel (E : Extension K A B) : Submodule K B := LinearMap.ker E.linear

/-- **Definition (unnumbered, p. 64) (singular)** (Hochschild). Kernel square zero
means that every product of two kernel elements vanishes. -/
def IsSingular (E : Extension K A B) : Prop :=
  ∀ x y : B, E.sigma x = 0 → E.sigma y = 0 → x * y = 0

/-- **Definition (unnumbered, p. 64) (segregated)** (Hochschild). The kernel has
an algebra complement isomorphic to `A`; `IsCompl` is the direct sum of vector
subspaces, not a claim that both summands are ideals. -/
def IsSegregated (E : Extension K A B) : Prop :=
  ∃ S : NonUnitalSubalgebra K B, IsCompl E.kernel S.toSubmodule ∧
    ∃ e : S ≃ₗ[K] A, ∀ x y : S, e (x * y) = e x * e y

/-- An algebra section of the extension homomorphism. Its equivalence with
segregation is proved separately rather than assumed in the definition. -/
def HasSection (E : Extension K A B) : Prop :=
  ∃ s : A →ₙₐ[K] B, ∀ a : A, E.sigma (s a) = a

end Extension
end Hochschild1945
