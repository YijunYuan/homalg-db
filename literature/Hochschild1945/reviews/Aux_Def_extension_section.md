# Independent review: algebra-section equivalence

## source-fidelity — 2026-10-28 root-section6-independent

Session: root-section6-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The editorial equivalence is proved for the literal nonunital direct-sum definition, without assuming singularity.

Source: Definition of segregation, printed p.64 / PDF8, independently inspected as an image. This auxiliary makes an elementary equivalence explicit rather than attributing a new theorem to the original paper.

| Clause | Evidence and assessment |
| --- | --- |
| Complement to section | The quotient restricted to the complementary subalgebra is bijective; its inverse is proved multiplicative. |
| Section to complement | The actual range subalgebra has zero intersection with the kernel and the decomposition b=(b-s(sigma(b)))+s(sigma(b)). |
| Scope | Arbitrary B; no unit, singularity or finite coefficient hypothesis. |

## honesty — 2026-10-28 root-section6-independent

Session: root-section6-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The section and range are constructed; neither implication assumes the desired complement.

| Check | Assessment |
| --- | --- |
| Witnesses | complementEquiv, its inverse algebra map and the actual range subalgebra supply the existential witnesses. |
| Proof | The Lean implementation uses ordinary linear algebra and multiplication preservation, with no local sorry. |
