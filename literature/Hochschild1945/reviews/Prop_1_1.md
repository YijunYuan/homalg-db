# Independent review: Prop_1_1

## source-fidelity — 2026-10-28 root-independent-pilot-review

Status: satisfactory
Verdict: The constructed module and existential theorem have exactly the printed left and twisted right actions, and verify them by expansion as the source requests.

| Source evidence, printed p. 59 | Lean representation | Assessment |
| --- | --- | --- |
| (a*f)(x)=a·f(x) | `homLeft`, `homLeft_apply` | Exact formula, linear in both inputs. |
| (f*a)(x)=f(ax)−f(a)·x | `homRight`, `homRight_apply` | Multiplication order and subtraction match the source. |
| Direct verification of right associativity | `homRight_assoc` | Expansion, the original module law and additive cancellation; no different cohomology argument. |
| Compatibility with the left action | `homLeft_right` | Uses the source two-sided action law. |
| One-cochains become a two-sided module | `twistedModule`, `one_cochains_two_sided` | A concrete witness with the stated operations, not just existence of some arbitrary module. |

The reviewer compared the complete pre-statement proof paragraph with reviewed
private PDF page 3 and inspected the bilinearity and three action-law proofs.

## honesty — 2026-10-28 root-independent-pilot-review

Status: satisfactory
Verdict: Every field of the new module is proved from the original module, and the existential conclusion exposes both required action formulae.

| Check | Evidence | Assessment |
| --- | --- | --- |
| Nonvacuous witness | `twistedModule M` with explicit actions | No arbitrary module or conclusion-shaped hypothesis. |
| Proof route | Direct linear-map extensionality, original action laws, cancellation | Matches the source's direct verification. |
| Unfinished assumptions | No `sorry`, axiom or added module-law premise | The original TwoSidedModule laws are the appropriate inputs. |


## source-fidelity — 2026-10-28 — ci-firstchapter-independent
Session: ci-firstchapter-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: The concrete left and twisted right actions are the displayed source operations, and their direct associativity and compatibility proofs establish the stated two-sided module.

| Source location / text | Current source excerpt | Comparison |
| --- | --- | --- |
| Printed p. 59 / PDF p. 3, paragraph preceding Proposition 1.1 and its displayed formulas | Current Statement and Proof reproduce both the formulas and their source explanation | The pre-statement proof placement is preserved. |

| Source hypothesis or conclusion | Lean representation | Comparison |
| --- | --- | --- |
| `(a*f)(x)=a·f(x)` | `homLeft_apply` | Literal equality. |
| `(f*a)(x)=f(ax)-f(a)·x` | `homRight_apply` | Multiplication order and subtraction agree exactly. |
| The operations give a two-sided module | `twistedModule` and `one_cochains_two_sided` | The witness is constructed; each of its law fields has a proof from the original module laws. |

| Definition used | Boundary / construction | Meaning checked |
| --- | --- | --- |
| Cochain degree one | Source carrier `A →ₗ[K] P` | No stronger notion is used. |
| `homLeft_assoc`, `homRight_assoc`, `homLeft_right` | Direct expansion, distributivity and source module identities | Matches the source’s direct-verification route; no external classification result is used. |

Findings: none. This independent review records agent evidence only; it does not manufacture a human approval. The finite-dimensional algebra context is evidenced by the finite basis in the following paragraph on the same page, and the coefficient space is not silently restricted to finite dimension.

## honesty — 2026-10-28 — ci-firstchapter-independent
Session: ci-firstchapter-independent
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: The output module laws are proved by expansion and cancellation. The existential witness is the explicit twistedModule; the proposition is not smuggled into a new input assumption.

| Object inspected | Classification | Evidence |
| --- | --- | --- |
| Main declarations and their referenced source definitions | Constructed data or proved source result | The output module laws are proved by expansion and cancellation. The existential witness is the explicit twistedModule; the proposition is not smuggled into a new input assumption. |

No sorry, extra asserted mathematical axiom, or theorem-conclusion packaging was found in these declarations and their source construction route. Compiled export was independently produced by the implementing math agent; this review additionally inspected the current Lean definitions/proofs and the reviewed source page.

## honesty — 2026-10-28 — /root/chapter1_honesty

Session: /root/chapter1_honesty
Author-session: /root/lean_fixtures
Status: satisfactory
Verdict: Proved producers and concrete source definitions; no hypothesis-packaging found.

Snapshot: ledger `364459b0e1a592df8c44ddda1ee1782875c38075`. The six scoped
Lean files were unchanged during this audit. The reviewer was the actual native
child task `/root/chapter1_honesty`; its shell inherited Horizon session
`0002-horizon-Hochschild1945.PROOF.1`.

Scope: `Def_two_sided_module`, `Def_cochain`, `Prop_1_1`, `Not_A_colon_P`,
`Bridge_Def_cochain_mathlib`, `Bridge_Def_two_sided_module_mathlib`, and the
consumers `delta` and `delta_evaluate_formula`.

| Check | Evidence and assessment |
| --- | --- |
| Source route | Visually inspected printed p. 59 / PDF page 3. `homLeft`, `homRight`, and their three action-law proofs implement the displayed operations by direct expansion. |
| Proposition witness | `twistedModule` constructs both actions and proves every law; `one_cochains_two_sided` exposes the required formulas. |
| Source objects | Positive-degree cochains are linear maps from iterated tensor products; degree zero is `P`. `AColonP` names the constructed module. |
| Cochain bridge | `cochainMultilinearEquiv` composes actual currying equivalences, and its evaluation theorem preserves tuples in every degree. |
| Module bridge | Both conversion maps construct the representations and preserve the action maps. Opposite multiplication correctly reverses the right action. |
| Consumer | `delta` recursively uses `twistedModule`; `delta_evaluate_formula` unfolds its actions to recover the alternating-sum formula. |
| Reachability | All six modules are imported by the document root, and graph attachments name the inspected declarations. |
| Trust | Fresh serialized axiom check passed, exit 0, fingerprint `9cbafd017438d26f`. All twelve declarations below use only `propext`, `Classical.choice`, and `Quot.sound`. |

The reviewer ran `horizon check --lean` on a scratch file containing:

```lean
import HomAlg.Hochschild1945.Bridge_Def_cochain_mathlib
import HomAlg.Hochschild1945.Bridge_Def_two_sided_module_mathlib
#print axioms Hochschild1945.TwoSidedModule
#print axioms Hochschild1945.cochainSpace
#print axioms Hochschild1945.twistedModule
#print axioms Hochschild1945.one_cochains_two_sided
#print axioms Hochschild1945.AColonP
#print axioms Hochschild1945.cochainMultilinearEquiv
#print axioms Hochschild1945.cochain_multilinear_equivalence
#print axioms Hochschild1945.cochainMultilinearEquiv_apply
#print axioms Hochschild1945.twoSidedActionsEquiv
#print axioms Hochschild1945.two_sided_module_bridge
#print axioms Hochschild1945.delta
#print axioms Hochschild1945.delta_evaluate_formula
```

Findings: no actionable integrity defect. These proofs existed before this
session. Frontier before/after: no unmet producer among the six scoped nodes;
the later cited obligations and Theorem 5.1 remain outside this task. Confidence:
high for the scoped honesty conclusion. This review does not create a new
fidelity lock or certify the whole paper.

### Lead verification — 0002-horizon-Hochschild1945.PROOF.1

`homalg stage-check Hochschild1945.PROOF.1 --json` exited 0 with
`complete: true`, no failures and no skipped stage checks. A serialized
`horizon check` naming all six scoped modules also exited 0. Proposition 1.1's
LSP diagnostics were empty. No Lean statement or proof was edited.

`make test`, `make validate`, and `make site` exited 0: 368 ordinary Python
tests passed with 17 skips, 31 frontend tests passed, and the separately enabled
19 Lean smoke/export tests passed. Validation reported zero errors, eight
existing warnings and 14 context-dependent skipped checks. The retained warnings
concern declared source dependencies and intentional Mathlib comparison targets;
the module bridge already explains its `NonUnitalAlgHom` warning. Lean's module
system advisories, Starlette/httpx and ESLint deprecations also remain visible.
These infrastructure warnings were left for their own scope.

The two exploratory `prune-check` calls exited 2 because bridges are retained
by that command; no auxiliary was created or deleted. The skill reconciliation
updated only the obsolete review-policy paragraphs in 18 local skills after an
independent comparison found all other bytes equal to the installed bundle.
