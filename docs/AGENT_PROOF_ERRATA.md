# Routine proof errata adjudicated by independent agents

This route records a new, limited **agent judgment** under prospective repository
policy. It does not record owner adoption, human confirmation, a fidelity review,
or a completed Lean proof. Human dispute commands and owner-decision replay keep
their existing guards. The feature must be installed before the native session
whose immutable START policy authorizes it. Public PR checks use BASE authority.

The original `proof-membership-target-typo` category permits one uniquely occurring
membership expression in a literal Proof, with the same subject and target base
symbol and only a changed prime adornment on that target. The exact relation must
fill one paired literal math span (`$...$`, `$$...$$`, `\(...\)`, or `\[...\]`),
with optional surrounding whitespace and at most one terminal comma, semicolon
or full stop. A complete bare Proof relation is also supported. Prefixes of longer
subjects/targets, added primes or scripts, compound expressions, escaped or
mismatched delimiters and fragments spanning separate math regions are refused. The two actual reviewers
must establish the unique correction from the source's local typed maps/binders,
with unchanged Statement, hypotheses, supporting data and proof route. An argument
repair, ambiguity, counterexample, missing evidence, or disagreement is ineligible.

The operation accepts only an ordinary theorem-like node with an unconfirmed open
proof dispute, current compiled theorem statements and all main proofs still
`sorry`-backed. It rejects statement/confirmed disputes, human or legacy fidelity
locks, foundations, auxiliary/cited/informal nodes, and nodes excluded by policy.
`CartanEilenberg1956.Prop_I_6_1` is explicitly excluded because the recorded problem
concerns an argument; a superficial membership replacement cannot admit it.
I.3.2 and II.4.5 have no approval from this infrastructure change. II.4.5 is only a
candidate for two new reviews of an actual frozen proposal.

## Source-bound proof map labels

The separate `proof-map-label-typo` category admits only the explicit
`ce1956-i3-2-extension-labels-v1` profile in `tools/homalg/proof_map_errata.py`.
It binds the node, source anchor, registered PDF, complete literal Statement and
Proof hashes, and one exact original/corrected passage. Its candidate correction
changes only the resulting extension's reference from `f''` to `f'` and its
antecedent from `f'` to `f_0`. The displayed defining equation and all other prose
remain unchanged. Neither eligibility nor installation decides that these are
the right labels: two new actual independent reviewers must establish this from
the source, current types, hypotheses, data and argument. Ambiguity or a required
mathematical repair must be escalated.

Select this class explicitly with `--category proof-map-label-typo` and supply
the profile's exact original and corrected strings. The default remains the
membership class. The new category and the exact profile digest must already be
present in the immutable native START policy. A session begun with the old
membership-only policy cannot acquire this authority through a mid-session
installation or policy edit. A different source transcription, statement,
argument, repeated passage or correction is refused, not generalized to a proof
rewrite. Changing the profile requires a separately reviewed tooling change and
a new prospective policy binding. I.6.1 remains explicitly excluded.

The same fresh compilation, real author provenance, two independent source and
data-impact assessments, exact acknowledgements, protected transaction/history
guards and ordinary post-adjudication reviews below apply. Each assessment's
`classification` must equal the proposal's selected category. Nodes without
compiled theorem statements remain ineligible. The tool only appends the typed
correction annotation and agent disposition; it never edits the literal Proof,
grants human attribution, supplies a proof or accepts the task.

## Native procedure

The canonical native lead must own an exact STMT task containing both the node and
its existing `literature/<Doc>/reviews/<Local>.md`, with proofs deferred in the
persisted document plan. Isolated draft workers cannot grant this decision.

1. Preserve the original author's collected native workspace and identify its real
   provider child/turn. `--author-workspace` names the registered workspace; the
   author event identifies the actual completed `node-writer` turn. The tool checks
   the collected write receipt, original native identity, source-ledger ancestry
   and current authored bytes. A later coordinator can preserve a genuine earlier
   author; no fictitious reauthoring or resumed dead child is required. If the
   retained delivery/ancestry cannot prove the current bytes, this route refuses.
   One separately committed canonical integration amendment may be supplied with
   `--integration-commit FULL_SHA`. It must directly follow the collected delivery
   and add only explicit HomAlg imports paired with statement-dependency entries;
   no removals, other metadata, comments, source prose or Lean commands may change.
   Its own native root command execution and matching parent observation are
   corroborated, excluding inherited child copies. The receipt separately credits
   the original writer and integrator and retains the exact before/after source.
   Both new reviewers must explicitly assess that amendment and the full current
   compiled claim/data. This is not an assumption that added imports are harmless.
2. Run `homalg dispute prepare-proof-erratum NODE --original TEXT --corrected TEXT
   --author-workspace WORKER --author-event CHILD_ID TURN_ID --out build/PROPOSAL.json`.
   The command performs a fresh full build/export and ordinary document validation,
   retaining the existing workflow's explicit derived-cache deferrals. It freezes
   the complete current compilation/context inputs, selected reviewed TeX and
   actual PDF/page-image bytes, original source/dispute/history, task and policy.
   The separate handoff and proposal are ignored build artifacts, not approvals.
3. Dispatch two independent `source-fidelity-reviewer` children before waiting.
   Each sees the same dossier, actual source images/TeX, Lean statements and
   supporting data, without the other's verdict. Both must be distinct from the
   actual author, integrator, coordinator and each other. Each writes its typed
   assessment to a distinct ignored build file and ends a fresh actual turn with
   the exact JSON acknowledgement below. The native lead then appends those exact
   blocks to the canonical report in one coordinated write. Do not have parallel
   reviewers edit the same report. Earlier source triage is not sufficient.
4. Run `homalg dispute adjudicate-proof-erratum NODE --snapshot build/PROPOSAL.json
   --reviewer-event CHILD_A TURN_A --reviewer-event CHILD_B TURN_B`. The tool joins
   actual provider-owned metadata, task start, assistant output, completion and
   native parent observation. Inherited fork history, arbitrary names, copied
   normalized text, wrong/old acknowledgements and unavailable execution evidence
   fail. This cooperative audit is not a cryptographic human signature.
5. On the final annotated bytes, perform fresh ordinary author preparation,
   independent source-fidelity and required honesty review, ordinary registration,
   generated graph/blueprint updates, exact stage checking and outer acceptance.
   Adjudication grants none of these gates. Proofs remain deferred.

## Typed assessment and acknowledgement

Append one JSON object in a `homalg-routine-proof-erratum-assessment` fenced block.
The exact required fields are:

```json
{
  "schema_version": 1,
  "kind": "routine-proof-erratum-assessment",
  "proposal_sha256": "PUBLIC_PROPOSAL_DIGEST_RETURNED_BY_PREPARE",
  "reviewer_session": "/root/ACTUAL_REVIEWER",
  "classification": "proof-membership-target-typo",
  "verdict": "unambiguous-local-typo",
  "unique_typing_justification": "Explain the exact local source binders/maps.",
  "comparisons": [
    "Compare the actual image, reviewed TeX and exact original/corrected membership.",
    "Compare the complete current Statement, hypotheses, Lean and supporting data."
  ],
  "impact": {
    "statement": "unchanged",
    "hypotheses": "unchanged",
    "data": "unchanged",
    "proof_route": "unchanged",
    "argument": "no_repair",
    "integration_amendment": "none"
  },
  "visual_sha256": "EXACT_PROPOSAL_VISUAL_DIGEST",
  "integration_amendment_sha256": "DIGEST_OF_AUTHOR_INTEGRATION_AMENDMENT_OR_NULL",
  "proof_approved": false
}
```

When an integration amendment is present, `impact.integration_amendment` must be
`reviewed-current-claim-and-data`, and its exact digest must match the proposal.
Each reviewer must supply substantive comparison of the amendment, current claim
and supporting data; merely recognizing the import text is insufficient.

These illustrative strings are not findings. Supply substantive comparisons and
actual provenance. Unknown fields and non-satisfactory classifications fail. The
reviewer's final assistant message must be the following JSON object, with no code
fence or surrounding prose; digests use the repository's canonical `json_text`
encoding through `homalg.owner_decisions.digest`:

```json
{
  "kind": "agent-proof-erratum-ack",
  "proposal_sha256": "EXACT_PUBLIC_PROPOSAL_DIGEST",
  "assessment_sha256": "EXACT_ASSESSMENT_OBJECT_DIGEST"
}
```

The public proposal digest covers `agent_errata._public(proposal)`. The complete
private snapshot remains ignored; the public projection retains source and source
identity, exact correction, task/policy, compiled statement hashes, original
writer and minimal execution bindings, plus hashes of private/global inputs.
Private text, raw prompts and the global compilation file list are not published.

## Application, history and recovery

Application appends a content-addressed `routine-proof-erratum-receipt` block and a
separate annotation under Formalization notes, adds an explained `erratum`
deviation, and records `resolution.kind: agent-routine-proof-erratum`. The literal
Statement and Proof remain intact. Only the primary active `PROOF-DISPUTED:` marker
is removed; all Lean commands, data, imports and proof bodies remain unchanged.
Old agent fidelity locks are cleared. Human/legacy locks are never replaced.

The native integration lock covers both report and node. All source/private/task/
proposal/report/execution inputs are rechecked before and after writes. Rollback
reverts only the tool's exact owned inodes; intervening foreign edits are retained
and a `recovery-required` journal blocks retry. An exact committed retry appends
nothing and preserves a subsequent ordinary fidelity lock. A different proposal,
review, correction or partial transaction cannot masquerade as that retry.

Native outer scope independently checks the audited task and START/end interval,
matching session metadata, committed application journal, exact full postimage,
and real reviewer execution again. Workers and hand-edited resolutions do not
receive the protected-field exemption merely by supplying a plausible receipt.

Historical validation checks original dispute, literal source/annotation, source
page/PDF identities and unchanged bound assessment blocks. Later ordinary review
may append new blocks. Editing or deleting an old bound block invalidates its
record. Reopening archives the exact former disposition once; forged/duplicate
history, deletion or kind downgrade fails. Historical records use their historical
evidence, not a later reopened Proof. A later genuinely reviewed Lean proof may
change the Lean body without inventing a new source-typo adjudication.

Public CI can verify these retained historical bindings without private source or
provider logs; it must not claim a fresh visual inspection. A new public PR
transition lacking trusted prior evidence remains owner-sensitive, as do changes
to typed receipt blocks. Current-session policy enablement never authorizes its own
formal task. This is distinct from local native routine progression and from the
existing human/owner-resolution protocols.
