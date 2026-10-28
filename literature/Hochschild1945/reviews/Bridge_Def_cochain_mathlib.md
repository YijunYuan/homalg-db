# Independent review: Bridge_Def_cochain_mathlib

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The tensor-linear cochain space has a genuine linear equivalence with Mathlib multilinear maps in every degree, preserving evaluation.

Source: Source cochains on printed p.59 / PDF3; editorial comparison bridge. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| Degree zero | `constLinearEquivOfIsEmpty` | A coefficient element becomes the constant map on the empty argument family. |
| Successor degree | `barEquiv, induction, multilinearCurryRightEquiv inverse` | Each step is an actual linear equivalence. |
| Evaluation | `cochainMultilinearEquiv_apply and pure tensor evaluation` | The correspondence preserves the supplied tuple, not merely dimensions. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: Both directions are built from linear equivalences; no dimension-only existence argument or renamed identity map replaces the source construction.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | Both directions are built from linear equivalences; no dimension-only existence argument or renamed identity map replaces the source construction. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
