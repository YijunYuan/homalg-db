# Independent review: Con_bar_map

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: Currying the final tensor factor gives the printed evaluation relation and is an actual linear equivalence.

Source: Construction in printed p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| m=1 identification | `barEquiv 0 is LinearEquiv.refl` | Matches the parenthetical degree-zero identification. |
| Positive tensor powers | `TensorProduct.lift.equiv inverse` | barEquiv_apply evaluates f(t ⊗ a), exactly the source formula. |
| Coefficient module | `Underlying carrier of (A:P)` | The source-only notation dependency is explained; its special actions enter delta. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The broader elementary linear-equivalence helper constructs both directions; it assumes neither the coboundary identity nor the dimension-shift theorem.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The broader elementary linear-equivalence helper constructs both directions; it assumes neither the coboundary identity nor the dimension-shift theorem. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
