## source-fidelity — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: The three named statements faithfully isolate the classical radical facts actually invoked on printed p. 64. Their proofs remain explicit external boundaries.

| Source usage / hypothesis | Lean expression | Independent comparison |
| --- | --- | --- |
| B/R is semisimple, printed p. 64 lower paragraph | `cited_radical_quotient`, `RadicalQuotient` | The bundled quotient map is surjective and has kernel exactly the Unitization/Jacobson radical, so this is a quotient of the input algebra, not an unrelated semisimple carrier. |
| N=K∩R is nilpotent | `cited_radical_nilpotent` | A positive length kills every product of elements in the actual radical. The use of the multiplicative inclusion into the unitization preserves all nonempty products. |
| S∩H={0} for a semisimple ideal | `cited_semisimple_inter_radical` | Requires an actual two-sided ideal and its semisimplicity, and concludes each element in the intersection is zero. It does not assume a complement. |
| Finite-dimensional possibly nonunital algebra | `FiniteDimensional K A`, `NonUnitalRing A` and scalar compatibility | Correct standing finite-dimensional setting. No identity in the source algebra is required. |

The editorial formulation is explicitly labeled and its source-evidence paragraph was compared with private page-0008.png. The nilpotence fact is the classical radical fact implicit in the printed assertion that K∩R is nilpotent. The nonunital radical foundation was independently checked in foundations-radical.md: the intersection of J(K⊕A) with A is the finite-dimensional nilpotent radical. The zero quotient is permitted, so the source's nilpotent special case is not silently excluded.

Findings: none.

## honesty — 2026-10-28 — ci-classical-section6-independent
Session: ci-classical-section6-independent
Author-session: schema-taxonomy-ideal-2026-10-28
Status: satisfactory
Verdict: Three explicit `sorry` declarations remain. The review approves their formulation and provenance as cited external facts, not completed proofs.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| `RadicalQuotient` | Genuine bundled quotient data | Actual algebra map, surjectivity, exact kernel, and promised semisimplicity; constructed only by the explicitly unproved cited theorem. |
| External facts | Visible cited proof boundaries | Three named `sorry` declarations; no axioms or hidden typeclass assumptions. |
| Nilpotent radical / intersection | Concrete predicates | Actual products and actual ideal/radical membership; no result supplied by an opaque user interface. |
