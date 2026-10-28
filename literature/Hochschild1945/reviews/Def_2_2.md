# Independent review: Def_2_2

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The predicates and subspaces agree exactly with vanishing coboundary and existence of a primitive.

Source: Definition2.2, printed p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| Cocycle | `IsCocycle n f := delta M n f = 0` | cocycles is its elementary linear kernel. |
| Positive-degree boundary | `Exists g, f = delta M n g` | mem_coboundaries proves the range convention has the same equality orientation. |
| Degree zero | `coboundaries 0 = bottom` | An explicit extension consistent with the separate H0 footnote; positive-degree source claims unchanged. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The subspaces arise from the authored linear map; closure is supplied by linear algebra rather than assumed source conclusions.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The subspaces arise from the authored linear map; closure is supplied by linear algebra rather than assumed source conclusions. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
