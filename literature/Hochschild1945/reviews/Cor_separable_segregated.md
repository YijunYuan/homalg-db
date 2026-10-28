# Independent review: Cor_separable_segregated

## source-fidelity — 2026-10-28 root-section6-independent

Session: root-section6-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The corollary follows the source chain Theorem4.1, the dimension-shift theorem and Theorem6.1, with finite extension scope explicit.

Source: p.67 / PDF11. The root reviewer inspected the rendered original pages, reviewed transcription and current Lean implementation.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Source separability | Uses the authored scalar-extension semisimplicity definition, not a substituted separability predicate. |
| H2 vanishing | The actual twisted module and degree-two dimensionShift reduce to H1 vanishing. |
| Scope | Segregation quantifies finite B; the general extension object and arbitrary coefficient spaces retain their meanings. |
| Proof boundary | The local proof is complete. Prop6.1 has since been proved relative to its classical citations and independently reviewed; the current remaining source proof gap is Thm4.1. No globally closed proof is claimed. |

## honesty — 2026-10-28 root-section6-independent

Session: root-section6-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The corollary follows the source chain Theorem4.1, the dimension-shift theorem and Theorem6.1, with finite extension scope explicit.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Source separability | Uses the authored scalar-extension semisimplicity definition, not a substituted separability predicate. |
| H2 vanishing | The actual twisted module and degree-two dimensionShift reduce to H1 vanishing. |
| Scope | Segregation quantifies finite B; the general extension object and arbitrary coefficient spaces retain their meanings. |
| Proof boundary | The local proof is complete. Prop6.1 has since been proved relative to its classical citations and independently reviewed; the current remaining source proof gap is Thm4.1. No globally closed proof is claimed. |

This is an actual independent agent review under the enabled policy. No human verdict is represented. The lock command must refresh compiled evidence before recording a lock.


## Proof-boundary update — 2026-10-28

The earlier inherited Theorem 4.1 gap is now closed. The root reviewer inspected
the complete two-direction construction against PDF pages 5–7 and recorded the
final independent report in `Thm_4_1.md`. Theorem 4.1 and both downstream
corollaries passed targeted Lean compilation. The corollary's local proof is
unchanged; its remaining logical proof boundaries are the explicitly identified
classical citations. This update preserves the earlier review history and does
not claim that those external citations have themselves been proved.
