# Independent review: Aux_Def_2_1_formula

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The proved all-degree formula matches the exact source alternating sum and validates the recursive implementation.

Source: Definition2.1 printed p.59 / PDF3 and currying identity p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| Arguments | `CochainArgs; head, tail, adjacent merge` | Last-factor tuple encoding retains argument order and adjacent multiplication. |
| Evaluation | `evaluateCochain_pureTensor` | Links tuple recursion to the actual tensor-linear map. |
| Signs and sum | `Fin n with exponent i.val+1, last exponent n+1` | Correct translation of one-based source indices. |
| Proof | `Induction, bar_delta, twisted right action, final sum split` | Recovers the last product and right-action terms with the correct signs. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The comparison is a kernel-checked theorem over all n and all source cochains; it is not a finite test or an equality assumed inside delta.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The comparison is a kernel-checked theorem over all n and all source cochains; it is not a finite test or an equality assumed inside delta. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
