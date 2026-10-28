# Independent review: Thm_3_1

## source-fidelity — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The quotient isomorphism is constructed from the source bar map and has exactly the printed degree range.

Source: Theorem3.1 and preceding proof, printed p.60 / PDF4. The reviewer compared the current Lean declarations with the private source images and independently reviewed transcription.

| Source clause or comparison | Lean evidence | Assessment |
| --- | --- | --- |
| m>=2 | `n+2 and fundamental_isomorphism m hm` | No positive degree is omitted and m=1 is not incorrectly asserted. |
| Cocycles | `barCocycles via bar_delta and inverse currying` | Both directions retain actual representatives. |
| Boundaries | `bar_mem_coboundaries and bar_boundaries_map` | Primitives are curried/uncurried explicitly; source reuses g across these spaces. |
| Cohomology isomorphism | `Submodule.Quotient.equiv and dimensionShift` | An actual linear equivalence descends the source map. |

## honesty — 2026-10-28 root-sections123-independent

Session: root-sections123-independent
Author-session: /root/lean_fixtures

Status: satisfactory
Verdict: The Nonempty theorem has an explicit dimensionShift witness with constructed inverse. The argument does not assume an isomorphism or replace the original proof by a standard Hochschild theorem.

| Check | Evidence |
| --- | --- |
| Hypotheses and definitions | The current source keeps nonunital finite-dimensional A and does not restrict P to finite dimension. |
| Actual construction or proof | The Nonempty theorem has an explicit dimensionShift witness with constructed inverse. The argument does not assume an isomorphism or replace the original proof by a standard Hochschild theorem. |
| Provenance | This is an actual independent root-agent review; its lock is recorded only after the command refreshes compiled evidence. No human approval is claimed. |
