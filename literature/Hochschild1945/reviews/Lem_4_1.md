# Independent review: Lem_4_1

## source-fidelity — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The finite-extension formulation is correct and now has a complete local proof; its finite scope and polynomial-descent variant are explicitly disclosed.

Source: pp.62–63 / PDF6–7. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Ground field | A prime p and CharP K p express nonzero positive characteristic; the L extension inherits this characteristic. |
| Conclusion | A nonzero K-linear D satisfying Leibniz is the source derivation. For commutative regular coefficients all inner derivations vanish, explaining the parenthetical. |
| Generality deviation | FiniteDimensional K L is explicitly narrower than the printed algebraic extension. It suffices for the finite center application. No assertion about author intent or human-confirmed new source error is made. |
| Why scope matters | In the perfect closure of F_p(t), every element is a pth power, so every derivation is zero although the algebraic extension is inseparable. |
| Proof boundary | A maximal proper intermediate field containing the relative separable closure makes the final step simple and purely inseparable. Its generator has inseparable irreducible minimal polynomial, hence derivative zero. Polynomial differentiation descends through evaluation, sends the generator to one and restricts to K. No sorry or cited theorem obligation remains. |

## honesty — 2026-10-28 root-section4-and-quotient-independent

Session: root-section4-and-quotient-independent
Author-session: /root/ci_governance

Status: satisfactory
Verdict: The finite-extension formulation is correct and now has a complete local proof; its finite scope and polynomial-descent variant are explicitly disclosed.

Source: pp.62–63 / PDF6–7. The root reviewer inspected the original page images, reviewed transcription, current Lean declarations and supporting definitions.

| Source clause / check | Lean evidence and assessment |
| --- | --- |
| Ground field | A prime p and CharP K p express nonzero positive characteristic; the L extension inherits this characteristic. |
| Conclusion | A nonzero K-linear D satisfying Leibniz is the source derivation. For commutative regular coefficients all inner derivations vanish, explaining the parenthetical. |
| Generality deviation | FiniteDimensional K L is explicitly narrower than the printed algebraic extension. It suffices for the finite center application. No assertion about author intent or human-confirmed new source error is made. |
| Why scope matters | In the perfect closure of F_p(t), every element is a pth power, so every derivation is zero although the algebraic extension is inseparable. |
| Proof boundary | A maximal proper intermediate field containing the relative separable closure makes the final step simple and purely inseparable. Its generator has inseparable irreducible minimal polynomial, hence derivative zero. Polynomial differentiation descends through evaluation, sends the generator to one and restricts to K. No sorry or cited theorem obligation remains. |

The actual statement author is /root/lean_fixtures; the final constructive proof was developed by /root/ci_governance with /root/lean_fixtures. The reviewer inspected the maximal-intermediate-field argument, actual polynomial quotient descent and nonzero witness. The proof-route deviation explicitly records that the separate assertions degree p and c^p in S were replaced by the zero-derivative descent criterion, without claiming those assertions were themselves proved.

The actual independent root-agent review is recorded under the enabled policy. It is not a human verdict. A normal review command must refresh compiled evidence before locking.
