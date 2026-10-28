# Theorem 5.1: a counterexample to the printed kernel identification

Author-session: /root/lean_fixtures
Session: thm51-counterexample-audit
Date: 2026-10-28

The printed statement and proof on pages 63–64 are preserved verbatim in the node. This report originally raised a source disagreement. The owner subsequently confirmed the source error and authorized recording the decision in the implementation conversation on 2026-10-28; see [the explicit owner decision](Thm_5_1-owner-decision.md). No corrected theorem or dispute resolution is claimed.

## Concrete data

Work over the rational field. Let A have basis a,b and identically zero multiplication, and let B be the ideal spanned by b. Both A and B are finite dimensional. Let P be the rational plane and write T(x,y)=(y,0). Define the four actions on basis elements by

| Action | Operator |
| --- | --- |
| left multiplication by a | T |
| left multiplication by b | T |
| right multiplication by a | 0 |
| right multiplication by b | T |

Extend all four actions linearly. Since T²=0, both associativity identities and the left/right compatibility identity in Definition 1 hold. Thus this is a two-sided module allowed by the actual source definition, even if one imposes finite dimensionality on P.

The two-sided annihilator Q of B is ker T, the line spanned by (1,0). The quotient A/B is the one-dimensional zero-product algebra. Its induced left and right actions on Q are zero.

## Cohomology calculation

Write a one-cochain as f(a)=x and f(b)=y. Evaluating the source cocycle equation at (a,a) gives Tx=0; at (a,b) it then gives Ty=0. Conversely those two equations imply the equations at (b,a) and (b,b), and bilinearity gives every equation. Hence Z¹(A,P)=Q×Q. The coboundary of u is (Tu,0), and T maps P onto Q. Consequently H¹(A,P) is Q, represented by the value at b.

For B, the cocycle equation is 2Ty=0, so Z¹(B,P)=Q over the rationals. Every B-coboundary is zero, since its two actions coincide. Restriction therefore identifies H¹(A,P) with H¹(B,P), and has zero kernel.

For A/B acting on Q, every linear map is a cocycle and every coboundary is zero. Thus H¹(A/B,Q)=Hom(A/B,Q) is a nonzero one-dimensional rational vector space. It cannot be isomorphic to the zero restriction kernel claimed in Theorem 5.1.

## Exact gap in the printed proof

Choose u=(0,1). The source coboundary f=δu has f(a)=(1,0) and f(b)=0. It is the zero class in H¹(A,P), and already vanishes on B. The resulting quotient cocycle has nonzero value (1,0) and is not a quotient coboundary.

The sentence asserting that the map f↦f* is determined up to a coboundary is the problematic step. Two choices of the correcting primitive differ by an element that commutes with B, meaning b·w=w·b. Such an element need not be annihilated on both sides by B. Here every w commutes with B, whereas only ker T is annihilated. Changing the primitive by u therefore changes the quotient cohomology class.

## Compiled evidence and its exact scope

`HomAlg/Hochschild1945/Aux_Thm_5_1_counterexample.lean` constructs the zero-product algebra and the actions as an actual `TwoSidedModule`. Its theorem `Hochschild1945.Counterexample5.primitive_dependence` proves, using the source `delta` and proved `delta_delta_zero`, that the displayed cochain is a coboundary and cocycle, vanishes on every element of B, and is not the coboundary of any primitive in the two-sided annihilator.

This Lean theorem verifies the representative-dependence witness directly. The complete quotient dimension calculation above is mathematical review evidence; it is not represented as a completed Lean quotient-isomorphism proof. The witness contains no `sorry` and does not use the disputed Theorem 5.1.

The calculation has also been independently checked by the root agent and the ci_governance agent. Their confirmations are recorded in the collaboration history; this author has not written review records impersonating either reviewer.

## Effect on the following corollary

The example does not refute the corollary's universal assertion over every P. In the source's historical usage, “isomorphism” here means an injection onto its image. A repaired proof can use the always-surjective inflation map from H¹(A/B,ann_B P) onto the restriction kernel; it need not be injective for general P. The reverse implication tests modules inflated from A/B, where B acts as zero on all of P and the primitive ambiguity disappears. This route needs its own formal proof and explicit deviation record; it must not invoke the false identification as a proved lemma.
