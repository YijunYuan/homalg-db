# Independent review: Lem_cocycle_subgroups

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The image of delta lies in its next kernel using the previously proved delta-square-zero lemma.

Source: Unnumbered subgroup statement, printed p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| Subgroup structure | `cocycles and coboundaries are Submodule values` | Their induced additive groups provide the stated closure. |
| Inclusion | `coboundaries_le_cocycles` | A represented boundary delta g maps to zero by delta_delta_zero. |
| Proof route | `Explicit source square-zero lemma` | No Mathlib cohomology shortcut or omitted defining dependency. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The principal theorem proves the required inclusion; subgroup closure is present in actual submodule structures. No vacuous predicate or hidden inclusion field is used.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The principal theorem proves the required inclusion; subgroup closure is present in actual submodule structures. No vacuous predicate or hidden inclusion field is used. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
