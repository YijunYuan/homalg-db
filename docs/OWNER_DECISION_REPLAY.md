# Replaying an existing owner instruction

An already adopted correction must not be asked again merely because its earlier
relay was not a protected human record. `owner-decision-replay` records the actual
agent's application of a bounded prior owner instruction. It is neither a human
confirmation nor a new adjudication, independent review, or completed formal proof.
The ordinary guarded human commands remain unchanged.

`horizon/owner-decision-replays.json` contains only five specifically adopted CE1956
corrections: the Chapter I p. 4 quotient target, p. 13 principal ideal domain wording,
Exercise I.6's `n > 1` hypothesis, Chapter III p. 50's two corrected proof summands,
and the Chapter I p. 15 coordinate remainder in Proposition 6.1's proof. The first
three bind the immutable relay projections of I-0022/23/24; the last two bind their
relay item, the actual decision artifact and the reviewed source page hashes. Inbox authorship is not evidence of a human signature: the separate receipt
truthfully identifies the outer operator attesting to the prior instruction.

At an idle administrative boundary, after installing the reviewed profile into the
source ledger, the outer coordinator can record each applicable receipt:

```sh
homalg record-owner-decision ce1956-i-p4 \
  --by ACTUAL-OPERATOR --session ACTUAL-OUTER-SESSION \
  --attest-existing-owner-instruction
```

The command checks exact evidence, node, source/PDF identity, original dispute,
original dispute history, literal statement and adopted correction. It creates an
append-only typed receipt under `literature/<DocKey>/owner-decisions/` and commits
only that receipt to the source ledger with an administrative relay message. It
cannot issue a different decision or run inside a native session or draft worker.
Delivery acknowledgements do not change a relay's identity. Changed mathematical
content, source identity or original evidence invalidates the binding.

A subsequent native canonical lead whose explicit task scope owns the node uses:

```sh
homalg dispute replay-owner-decision CartanEilenberg1956.Con_I_short_exact_sequence_normalization \
  --decision ce1956-i-p4 --by ACTUAL-AGENT --session ACTUAL-NATIVE-SESSION
```

The native session must start after the profile and receipt were committed. A
same-session receipt, including one committed midway through the session, confers
no authority. The engine's final scope check independently uses its actual start
commit; PR validation uses its immutable merge base. Receipt/profile changes are
forbidden in native scopes, even when explicitly included in a task's write set,
and remain owner-sensitive in PR classification. A receipt must be present in the
PR base before a PR can use it to resolve a node. These are cooperative repository
and process boundaries, not cryptographic authentication of the owner's identity.

An isolated native session may validate an existing resolution. Its actual live
parent, task identity and held run lease are checked before reading session-start
metadata, inbox evidence and hash-bound historical artifacts from the canonical
control directory. This includes private source pages and ignored build evidence
that are shared or absent in the isolated checkout. Policies and receipts still
come from the isolated source checkout and its immutable start commit. Shared
runtime mounts do not authorize symlinked
evidence files, a different control directory, or replay writes from the isolated
session; the ordinary no-symlink checks and replay restrictions remain in force.

Replay retains the original dispute fields and history, adds a separately typed
resolution with the actual agent/session and receipt digest, removes its active
docstring dispute marker, and invalidates any existing agent fidelity lock. It
cannot replace a human or legacy human lock. Draft workers cannot perform replay.
An idle outer replay is also supported and leaves its node edit for the normal
integration commit; it does not manufacture a human ledger action.

A profile may carry the adopted correction itself in its `correction` field: the
erratum deviation and, for a proof dispute, a Formalization-notes paragraph with
explicitly labelled corrected displays (`\tag{..., corrected}`). This covers an
owner decision made before any session wrote the correction. The binding is computed
over the node with that correction applied; attestation does not edit the node, and
the replay writes exactly the pinned text before resolving the dispute. The owner
therefore does not need a guarded terminal command, and no idle boundary is needed
between authoring the correction and replaying it. Any other change to the pinned
text or to the literal source makes the receipt stale.

The fourth profile binds the complete literal proof and the two explicitly labelled
corrected displays in Formalization notes. Those displays are not a replacement
proof. This receipt authorizes only the adopted textual erratum, preserves the
statement and original proof, and does not authorize a proof-route change.

Compile current code and obtain ordinary independent fidelity/honesty review after
replay. The receipt and profile are frozen review inputs. The stage, source prose,
DAG, source fidelity and full-book acceptance obligations remain in force. A later
new disagreement is opened normally, preserving the exact prior replay in history;
replay history cannot be fabricated or used as authority for a new correction.
