import HomAlg.Hochschild1945.Def_two_sided_module
import HomAlg.Hochschild1945.Def_cochain
import Mathlib.Tactic.Abel

/-!
```yaml node
id: "Hochschild1945.Prop_1_1"
doc: "Hochschild1945"
kind: "proposition"
source:
  label: "Proposition 1.1"
  pages:
    - 59
  chapter: "1"
tags:
  - "cohomology"
  - "module"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Def_cochain"
    - "Hochschild1945.Def_two_sided_module"
  proof: []
decls:
  - "Hochschild1945.one_cochains_two_sided"
  - "Hochschild1945.twistedModule"
fidelity:
  status: "faithful"
  reviewed:
    by: "ci-governance"
    kind: "agent"
    status: "satisfactory"
    on: "2026-10-28"
    decl_hashes:
      Hochschild1945.one_cochains_two_sided:
        statement_sha256: "340fa854c23111621805f024ec4727ea8daa53446c77c33518a1cac27b437a4b"
        type_hash: "000000004e9e1de0"
        meaning_hash: "8992d1d989c9d198"
      Hochschild1945.twistedModule:
        statement_sha256: "615231ee5e0143a4d506733e8170960d1c2115402b7b66f1e7745159dcedac2a"
        type_hash: "000000007d350c47"
        meaning_hash: "1777c6104649fcd1"
    session: "ci-firstchapter-independent"
    author_session: "/root/lean_fixtures"
title: "Two-sided module of one-cochains"
```

## Statement

The linear space $(\mathfrak{A}^{(1)}:\mathfrak{P})$ of the $(1,\mathfrak{P})$-cochains of $\mathfrak{A}$ is a
two-sided $\mathfrak{A}$-module with the operations $f\to a*f$ and $f\to f*a$, where
\[
(a*f)\{a'\}=a\cdot f\{a'\}\quad\hbox{and}
\]
\[
(f*a)\{a'\}=f\{aa'\}-f\{a\}\cdot a'.
\]

## Proof

The linear space $(\mathfrak{A}^{(1)}:\mathfrak{P})$ formed by the $(1,\mathfrak{P})$-cochains of
$\mathfrak{A}$ will play an important part in what follows. We make $(\mathfrak{A}^{(1)}:\mathfrak{P})$
into a two-sided $\mathfrak{A}$-module in a way specially adapted to our purpose: If
$f\in(\mathfrak{A}^{(1)}:\mathfrak{P})$ and $a\in\mathfrak{A}$ we define an element $a*f$ of
$(\mathfrak{A}^{(1)}:\mathfrak{P})$ as follows: $(a*f)\{a'\}=a\cdot f\{a'\}$, for every
$a'\in\mathfrak{A}$. Clearly, this makes $(\mathfrak{A}^{(1)}:\mathfrak{P})$ into an $\mathfrak{A}$-left module.
Furthermore, we define an element $f*a$ of $(\mathfrak{A}^{(1)}:\mathfrak{P})$ by setting
$(f*a)\{a'\}=f\{aa'\}-f\{a\}\cdot a'$, for every $a'\in\mathfrak{A}$. It can be
verified directly that the operation $f\to f*a$ makes $(\mathfrak{A}^{(1)}:\mathfrak{P})$ into
an $\mathfrak{A}$-right module and that $(\mathfrak{A}^{(1)}:\mathfrak{P})$ has in fact become a two-sided
$\mathfrak{A}$-module. We state these facts in the following proposition:

## Description

The source construction is retained with an associative algebra without a required identity. Tensor products and linear maps supply basic linear algebra only; no existing cohomology construction is substituted.
-/


namespace Hochschild1945

universe u

variable {K A P : Type u} [Field K] [NonUnitalRing A] [Module K A]
  [SMulCommClass K A A] [IsScalarTower K A A] [FiniteDimensional K A]
  [AddCommGroup P] [Module K P] (M : TwoSidedModule K A P)

/-- The source's left action on one-cochains, `(a * f)(x) = a · f(x)`. -/
def homLeft : A →ₗ[K] (A →ₗ[K] P) →ₗ[K] (A →ₗ[K] P) :=
  LinearMap.mk₂ K (fun a f => (M.left a).comp f)
    (by intros; ext; simp)
    (by intros; ext; simp)
    (by intros; ext; simp)
    (by intros; ext; simp)

/-- The source's twisted right action, `(f * a)(x) = f(ax) - f(a) · x`. -/
def homRight : (A →ₗ[K] P) →ₗ[K] A →ₗ[K] (A →ₗ[K] P) :=
  LinearMap.mk₂ K (fun f a => f.comp (LinearMap.mul K A a) - M.right (f a))
    (by intros; ext; simp; abel)
    (by intros; ext; simp [smul_sub])
    (by intros; ext; simp; abel)
    (by intros; ext; simp [smul_sub])

/-- Evaluation of the left action is the displayed formula of Proposition 1.1. -/
@[simp] theorem homLeft_apply (a x : A) (f : A →ₗ[K] P) :
    homLeft M a f x = M.left a (f x) := rfl

/-- Evaluation of the right action is the displayed formula of Proposition 1.1. -/
@[simp] theorem homRight_apply (a x : A) (f : A →ₗ[K] P) :
    homRight M f a x = f (a * x) - M.right (f a) x := rfl

/-- The source's direct verification of associativity of its left action. -/
theorem homLeft_assoc (a b : A) (f : A →ₗ[K] P) :
    homLeft M (a * b) f = homLeft M a (homLeft M b f) := by
  ext x
  exact M.left_assoc a b (f x)

/-- The source's direct verification of associativity of its twisted right action.
Expanding twice cancels the two terms `f(a) · (bx)` by the original right-module law. -/
theorem homRight_assoc (f : A →ₗ[K] P) (a b : A) :
    homRight M (homRight M f a) b = homRight M f (a * b) := by
  ext x
  simp only [homRight_apply, map_sub, LinearMap.sub_apply, M.right_assoc, mul_assoc]
  abel

/-- The source's direct verification of compatibility of left and right actions. -/
theorem homLeft_right (a b : A) (f : A →ₗ[K] P) :
    homRight M (homLeft M a f) b = homLeft M a (homRight M f b) := by
  ext x
  simp only [homRight_apply, homLeft_apply, map_sub, M.left_right]

/-- **Proposition 1.1**. The printed left and twisted right actions make the
space of one-cochains a two-sided module. The preceding direct expansions verify every law. -/
def twistedModule : TwoSidedModule K A (Cochain K A P 1) where
  left := homLeft M
  right := homRight M
  left_assoc := homLeft_assoc M
  right_assoc := homRight_assoc M
  left_right := fun a f b => homLeft_right M a b f

/-- **Proposition 1.1**. There is a two-sided module on the source's one-cochains
whose operations are precisely the two displayed formulas. The witness is the directly
verified construction above, rather than an assumed module structure. -/
theorem one_cochains_two_sided :
    ∃ N : TwoSidedModule K A (Cochain K A P 1),
      (∀ (a x : A) (f : A →ₗ[K] P), N.left a f x = M.left a (f x)) ∧
      (∀ (f : A →ₗ[K] P) (a x : A), N.right f a x = f (a * x) - M.right (f a) x) :=
  ⟨twistedModule M, fun _ _ _ => rfl, fun _ _ _ => rfl⟩

end Hochschild1945
