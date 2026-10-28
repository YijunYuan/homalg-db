import HomAlg.Hochschild1945.Aux_Thm_5_1_quotient_module
import HomAlg.Hochschild1945.Def_2_3
import HomAlg.Hochschild1945.Def_natural_homomorphism
import HomAlg.Hochschild1945.Def_two_sided_module
import Mathlib.LinearAlgebra.Isomorphisms

/-!
```yaml node
id: "Hochschild1945.Thm_5_1"
doc: "Hochschild1945"
kind: "theorem"
source:
  label: "Theorem 5.1"
  pages:
    - 63
    - 64
  chapter: "5"
tags:
  - "hochschild-cohomology"
concepts:
  defines: []
  uses: []
deps:
  statement:
    - "Hochschild1945.Aux_Thm_5_1_quotient_module"
    - "Hochschild1945.Def_2_3"
    - "Hochschild1945.Def_natural_homomorphism"
    - "Hochschild1945.Def_two_sided_module"
  proof: []
decls:
  - "Hochschild1945.restriction_kernel_isomorphism"
fidelity:
  status: "faithful"
title: "Kernel of the natural homomorphism"
dispute:
  status: "open"
  kind: "statement"
  reason: "Over a two-dimensional zero-product rational algebra, the restriction kernel is zero but H1
    of the quotient with the two-sided annihilator is one-dimensional; see reviews/Thm_5_1.md and Aux_Thm_5_1_counterexample.
    The printed primitive-independence step fails."
  on: "2026-10-28"
  opened_by: "lean-fixtures"
  inbox: "I-0001"
  confirmed_by: "YijunYuan"
  confirmed_on: "2026-10-28"
```

## Statement

Let $\mathfrak{Q}$ be the subspace of $\mathfrak{P}$ which is annihilated by $\mathfrak{B}$. Then the kernel of the natural homomorphism of $H^1(\mathfrak{A},\mathfrak{P})$ into $H^1(\mathfrak{B},\mathfrak{P})$ is isomorphic with $H^1(\mathfrak{A}/\mathfrak{B},\mathfrak{Q})$, where $\mathfrak{Q}$ is regarded as a two-sided $\mathfrak{A}/\mathfrak{B}$-module.

## Proof

If $f$ is a 1-dimensional $\mathfrak{P}$-cocycle of $\mathfrak{A}$ which cobounds in $\mathfrak{B}$ there exists an element $u\in\mathfrak{P}$ such that $f\{b\}=b\cdot u-u\cdot b$, for every $b\in\mathfrak{B}$. Consider the $(1,\mathfrak{P})$-cocycle $f'$ of $\mathfrak{A}$ defined by: $f'\{a\}=f\{a\}-a\cdot u+u\cdot a$. Then $f'\{b\}=0$, for every $b\in\mathfrak{B}$, i.e. $\hat f'=0$. Furthermore, $b\cdot f'\{a\}-f'\{ba\}+f'\{b\}\cdot a=0$, since $f'$ is a cocycle. This reduces to $b\cdot f'\{a\}=0$, and similarly, $f'\{a\}\cdot b=0$, for all $b\in\mathfrak{B}$ and all $a\in\mathfrak{A}$. Thus $f'$ maps $\mathfrak{A}$ into $\mathfrak{Q}$. Clearly, $f'$ may be regarded as a $(1,\mathfrak{Q})$-cocycle $f^*$ of $\mathfrak{A}/\mathfrak{B}$. If $f^*$ cobounds there exists an element $v\in\mathfrak{Q}$ such that $f^*\{a\}=a\cdot v-v\cdot a$. But then $f\{a\}=a\cdot(u+v)-(u+v)\cdot a$, i.e. $f$ cobounds. Hence the mapping $f\to f^*$, which is determined to within a coboundary, defines an isomorphism of the kernel of our homomorphism $H^1(\mathfrak{A},\mathfrak{p})\to H^1(\mathfrak{B},\mathfrak{p})$ into $H^1(\mathfrak{A}/\mathfrak{B},\mathfrak{Q})$.

Finally, if $h^*$ is any $(1,\mathfrak{Q})$-cocycle of $\mathfrak{A}/\mathfrak{B}$ we can define a $(1,\mathfrak{P})$-cochain $h$ of $\mathfrak{A}$ by the relation $h\{a\}=h^*\{\bar a\}$, where $\bar a$ is the coset of $a\bmod\mathfrak{B}$. It is easily seen that $h$ is actually a cocycle which vanishes on $\mathfrak{B}$. Obviously, $h$ is mapped into $h^*$ by the above isomorphism, which is therefore an isomorphism \emph{onto} $H^1(\mathfrak{A}/\mathfrak{B},\mathfrak{Q})$. This proves Theorem 5.1.

## Description

Identifies the kernel of restriction in degree one with quotient-algebra cohomology in the annihilated subspace.

## Formalization notes

The first line on printed page 64 uses lowercase Fraktur p; the transcription preserves that printed glyph rather than silently changing it.
A surjective nonunital algebra homomorphism π:A→C presents the quotient A/ker π. The kernel ideal, two-sided annihilator, and its quotient-algebra actions are actual constructions with proved laws, now isolated in Aux_Thm_5_1_quotient_module so their users do not logically depend on the false theorem. The displayed theorem is the literal printed assertion, not a corrected statement. The owner confirmed this statement error in the implementation conversation on 2026-10-28 and explicitly authorized recording the decision; see reviews/Thm_5_1-owner-decision.md. It remains an explicitly named unproved declaration under the confirmed open dispute I-0001; see reviews/Thm_5_1.md and Aux_Thm_5_1_counterexample. No later proof may use the disputed isomorphism as established evidence.
-/

namespace Hochschild1945

universe u

variable {K A C P : Type u} [Field K]
  [NonUnitalRing A] [Module K A] [SMulCommClass K A A] [IsScalarTower K A A]
  [FiniteDimensional K A]
  [NonUnitalRing C] [Module K C] [SMulCommClass K C C] [IsScalarTower K C C]
  [FiniteDimensional K C]
  [AddCommGroup P] [Module K P]

attribute [local instance] idealFiniteDimensional

/-- **Theorem 5.1** (Hochschild). This is the literal printed claim, using any
surjective presentation C of A/B and the actual annihilator module. The printed
proof subtracts an inner primitive to make a cocycle vanish on B, then claims
that the resulting quotient class is independent of the primitive.
STATEMENT-DISPUTED: primitive independence fails; see the counterexample report
and the closed source-differential witness in Aux_Thm_5_1_counterexample. This
named obligation is intentionally unproved and must not be used as evidence. -/
theorem restriction_kernel_isomorphism (M : TwoSidedModule K A P)
    (π : A →ₙₐ[K] C) (hπ : Function.Surjective π) :
    Nonempty ((LinearMap.ker (naturalHomomorphism M (kernelIdeal π) 1)) ≃ₗ[K]
      Cohomology (quotientAnnihilatorModule M π hπ) 1) := by
  sorry

end Hochschild1945
