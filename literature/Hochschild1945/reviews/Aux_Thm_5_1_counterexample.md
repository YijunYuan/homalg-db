# Independent review: primitive dependence witness

## source-fidelity — 2026-10-28 root-counterexample-independent

Session: root-counterexample-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The editorial counterexample uses the actual source bimodule and differential and disproves the asserted primitive-independence step.

Source: Theorem5.1 proof, printed pp.63–64 / PDF7–8; original source and the full independent dimension calculation are preserved in Thm_5_1.md. The owner confirmed the source error in Thm_5_1-owner-decision.md.

| Clause | Evidence and assessment |
| --- | --- |
| Algebra | Rational plane with zero multiplication; finite dimensional and nonunital, as allowed by the source. |
| Module | L_a=L_b=R_b=T, R_a=0, T(x,y)=(y,0); T squared zero verifies all three laws. |
| Witness | The actual delta of (0,1) is (r,s) mapped to (r,0), vanishes on every (0,t), and is a cocycle by the source delta-squared theorem. |
| Nonexistence | An annihilated primitive has second coordinate zero, contradicting witness(a)=(1,0). |

## honesty — 2026-10-28 root-counterexample-independent

Session: root-counterexample-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The compiled theorem proves the explicit witness, with no reliance on the disputed Theorem5.1; the full quotient dimension calculation is not claimed to be formalized.

| Check | Assessment |
| --- | --- |
| Concrete data | Actual ring/module instances and vectors, not an assumed counterexample structure. |
| Scope of conclusion | Failure of primitive independence is formally proved; the nonisomorphism of complete quotient groups remains independently checked mathematical evidence. |
| Independence | Root independently computed Z1(A,P)=Q times Q, B1(A,P)=Q times zero, and restriction as an isomorphism, while H1(A/B,Q) has dimension one. |
| Error boundary | Only the auxiliary is locked satisfactory; the source theorem keeps its owner-confirmed open dispute. |
