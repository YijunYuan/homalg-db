This is HomAlgDB, a source-faithful Lean literature database using the pinned
`homalg-horizon` fork. Read `AGENTS.md` first, then `HomAlg/AGENTS.md` when editing
Lean nodes and `docs/ENGINE.md` for the local runtime.

For a Horizon session, read `.claude/skills/horizon/SKILL.md` installed by
`homalg horizon-init`. If it is missing, report the missing setup before running
the engine. Keep its session and ledger conventions together with the repository's
source fidelity and task scope rules. The user override dated 2026-10-28 permits
independent agent reviews for foundations, first-chapter checkpoints and explained
deviations under the enabled `horizon/review-policy.yaml` policy. Follow
`docs/playbooks/review-fidelity.md`, record actual distinct author/reviewer sessions
and keep unresolved mathematical decisions human-only. Previously adopted decisions
may use the typed relay in `docs/OWNER_DECISION_REPLAY.md`, never a fabricated human
record. Dispatch independent ready workers before
joining their results; wait where their output is needed and before ending the
session. Follow the assigned task and the relevant `docs/playbooks/` guide.
Use scoped mathematical checks and the engine-owned finalization protocol; run
full tooling/site regressions only for tooling/schema/site changes, as specified
in `AGENTS.md`. Deferred formal proofs do not defer source proof prose or DAG,
metadata, review and generated-blueprint obligations.

Headers are authored truth; blueprint files and exported JSON are generated.
Coordinate parallel preparation through `docs/PARALLEL_WORKFLOW.md`: use isolated
draft ownership, frozen review inputs and actual independent reviewer provenance.
Compilation, promotion and hash validation do not replace review or final gates.
Use reviewed private page transcriptions for node excerpts. During a run build
through `horizon check`, commit only to `hgit`, and use the local inbox for issues.
Do not invoke human guards or write their protected fields. Publish document work
only through `homalg submit` after the engine is idle.
