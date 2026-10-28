# Independent review: Def_H0

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The degree-zero subgroup is exactly the elements with equal left and right actions against every algebra element.

Source: Footnote6, printed p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| All algebra elements | `forall a, left a p = right p a` | No centrality or identity condition on A is substituted. |
| Additive subgroup | `Actual Submodule carrier and closure proofs` | A stronger available linear structure retains the exact underlying subgroup. |
| Consistency | `degreeZeroGroup_eq_cocycles` | Proved from the degree-zero difference formula. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The equality with cocycles is proved in both directions. The definition neither assumes a later cohomology fact nor uses a placeholder carrier.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The equality with cocycles is proved in both directions. The definition neither assumes a later cohomology fact nor uses a placeholder carrier. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
