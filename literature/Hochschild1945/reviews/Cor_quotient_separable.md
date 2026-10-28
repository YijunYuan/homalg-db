# Independent review: Cor_quotient_separable

## source-fidelity — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The exact injectivity criterion has a complete local proof through a justified repaired route.

Source: p.64 / PDF8. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Historical wording | The surrounding zero-kernel argument and source usage of isomorphic mappings support injectivity onto the image. Surjectivity of restriction is not asserted. |
| Quotient and coefficients | A genuine surjective algebra map presents A/B. The theorem quantifies over all two-sided A-modules P without finite P. |
| Forward proof | Subtract the primitive of the restriction, obtain annihilator-valued cocycle vanishing on B, descend, and use Thm4.1 to choose one primitive. No primitive-independent cohomology assignment is needed. |
| Reverse proof | Inflate a quotient cocycle on a quotient module. Its zero restriction and the hypothesized injectivity imply a primitive, which works downstairs by surjectivity. |
| Source and formal routes | The original Thm5.1 edge and paragraph remain as source-only evidence, with proof-route deviation explicitly declared. The compiled proof never applies the false theorem. |
| Remaining boundary | The proof has no local sorry, but inherits the explicitly unproved Thm4.1. This review does not claim global proof completeness. |

## honesty — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The exact injectivity criterion has a complete local proof through a justified repaired route.

Source: p.64 / PDF8. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Historical wording | The surrounding zero-kernel argument and source usage of isomorphic mappings support injectivity onto the image. Surjectivity of restriction is not asserted. |
| Quotient and coefficients | A genuine surjective algebra map presents A/B. The theorem quantifies over all two-sided A-modules P without finite P. |
| Forward proof | Subtract the primitive of the restriction, obtain annihilator-valued cocycle vanishing on B, descend, and use Thm4.1 to choose one primitive. No primitive-independent cohomology assignment is needed. |
| Reverse proof | Inflate a quotient cocycle on a quotient module. Its zero restriction and the hypothesized injectivity imply a primitive, which works downstairs by surjectivity. |
| Source and formal routes | The original Thm5.1 edge and paragraph remain as source-only evidence, with proof-route deviation explicitly declared. The compiled proof never applies the false theorem. |
| Remaining boundary | The proof has no local sorry, but inherits the explicitly unproved Thm4.1. This review does not claim global proof completeness. |

The actual independent root-agent review is recorded under the enabled policy. It is not a human verdict. A normal review command must refresh compiled evidence before locking.

Actual coauthors: /root/lean_fixtures supplied the statement/support formulation; /root/ci_governance completed the constructive proof. The root reviewer independently inspected both.


## Proof-boundary update — 2026-10-28

The earlier inherited Theorem 4.1 gap is now closed. The root reviewer inspected
the complete two-direction construction against PDF pages 5–7 and recorded the
final independent report in `Thm_4_1.md`. Theorem 4.1 and both downstream
corollaries passed targeted Lean compilation. The corollary's local proof is
unchanged; its remaining logical proof boundaries are the explicitly identified
classical citations. This update preserves the earlier review history and does
not claim that those external citations have themselves been proved.
