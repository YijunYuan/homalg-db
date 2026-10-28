## source-fidelity — 2026-10-28 — ci-simple-component-independent
Session: ci-simple-component-independent
Author-session: /root
Status: satisfactory
Verdict: The editorial statement makes explicit the classical simple-component reduction invoked on printed p. 62. The actual ideal and algebra retraction express a direct algebra factor without assuming any cohomological conclusion.

| Source usage / hypothesis | Lean expression | Independent comparison |
| --- | --- | --- |
| A semisimple inseparable algebra has an inseparable simple component, printed p. 62 | `hsemi`, `hins`, and the existential `I : AlgebraIdeal K A` | The ambient and component separability predicates are the article's scalar-extension definition. The component is an actual scalar-closed two-sided ideal. |
| A simple component is nonzero and simple | `Nontrivial I.subalgebra` and the zero-or-top condition on all its two-sided ideals | Excludes the zero factor and states two-sided algebra simplicity explicitly. |
| The component of a semisimple algebra is semisimple | `Semisimple K I.subalgebra` | This is part of the classical component structure, not a new conclusion about cohomology. Finite dimension of the component follows from its embedding into finite-dimensional A. |
| The source trivially extends a component cocycle to A | An actual nonunital algebra projection `π : A → I` fixing every element of I | An ideal plus this retraction is a genuine direct algebra factor: the kernel complements I, and their products in both orders vanish. Inflation and recovery of a primitive remain separate checked proof steps. |
| Source standing algebra scope | Finite-dimensional associative nonunital K-algebra with compatible scalar action | No unit, characteristic, perfect-field, or finite coefficient-module hypothesis is added. |

I inspected private `page-0006.png` directly. The relevant paragraph immediately follows the invariant-complement proof and precedes the center-field reduction. It explicitly invokes an inseparable simple component and trivial extension of a non-cobounding component cocycle. The editorial formulation faithfully exposes the structural fact used there; it does not attribute a proof to the source or invent an external bibliographic theorem locator.

Findings: none concerning mathematical scope or source correspondence.

## honesty — 2026-10-28 — ci-simple-component-independent
Session: ci-simple-component-independent
Author-session: /root
Status: satisfactory
Verdict: One named cited `sorry` is retained as an explicit external boundary. This review approves the formulation and provenance, not a proof of the classical decomposition theorem.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| Component | Actual mathematical object | `AlgebraIdeal` includes a scalar-closed subalgebra and both absorption laws. |
| Direct-factor structure | Actual maps and equations | The nonunital algebra homomorphism fixes the actual ideal inclusion. This implies zero intersection with its kernel and full sum with that kernel. |
| Unproved content | Explicit classical citation | One visible `sorry`; no extra axiom, fabricated approval, or hidden derivation/cohomology assumption. |
| Subsequent source proof | Still separate | The theorem does not assert a non-inner cocycle or vanishing/nonvanishing of H¹. |
