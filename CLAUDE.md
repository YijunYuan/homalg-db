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
and keep unresolved disputes human-only. Run foreground work
to completion. Follow the assigned task and the relevant `docs/playbooks/` guide.

Headers are authored truth; blueprint files and exported JSON are generated.
Use reviewed private page transcriptions for node excerpts. During a run build
through `horizon check`, commit only to `hgit`, and use the local inbox for issues.
Do not invoke human guards or write their protected fields. Publish document work
only through `homalg submit` after the engine is idle.
