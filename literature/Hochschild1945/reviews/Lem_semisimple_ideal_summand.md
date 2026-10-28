## source-fidelity — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: The proof follows the printed radical-quotient, image-complement and inverse-image argument on pp. 64–65. The local proof is complete relative to the separately identified classical cited boundaries.

| Source step / hypothesis | Lean expression | Independent comparison |
| --- | --- | --- |
| S is a semisimple ideal in C | `I : AlgebraIdeal K A`, `hI : Semisimple K I.subalgebra` | Actual ideal and actual finite-dimensional semisimplicity, with no semisimplicity assumption on the ambient algebra. |
| Pass to C/H | `cited_radical_quotient`, `Q.quotient` | Surjective multiplicative K-linear map with kernel exactly the radical. |
| Complement (S+H)/H in C/H | `I.mapSurjective`, `cited_semisimple_ideal_structure` | The image is proved to be an ideal; a complement is obtained only in the semisimple quotient, as in the source. |
| Lift U to T | `J.comap Q.quotient` | Inverse image is explicitly constructed and its two-sided ideal laws proved. |
| T∩S=0 | Disjointness proof and `cited_semisimple_inter_radical` | An element maps to the intersection of complementary quotient ideals, hence lies in the radical and must be zero. |
| C=S+T | `Submodule.codisjoint_iff_exists_add_eq` | Decompose q(a), lift the image component to s∈S, and show a−s lies in the inverse-image ideal. This fills the printed final inference. |

The statement and proof excerpts were compared with the private images page-0008.png and page-0009.png, including their page boundary. The finite-dimensional ambient scope is the standing source convention needed for the radical theorem. The displayed source proof is preserved, and the local Lean proof uses its same route.

Findings: none.

## honesty — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: The local theorem has no `sorry`. Its proof still depends on the explicit cited classical results, whose unproved status remains visible; it must not be reported as a proof closed without those boundaries.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| `mapSurjective` / `comap` | Proved ideal constructions | Their fields contain only algebraic closure laws and are proved from multiplication and ideal absorption. |
| Radical quotient | Genuine quotient data | The kernel identity and surjectivity are used to establish intersection and spanning, not assumed final complements. |
| Complement proof | Locally complete proof with cited dependencies | Actual witness J.comap; no local `sorry`, no circular use of the general conclusion. |
