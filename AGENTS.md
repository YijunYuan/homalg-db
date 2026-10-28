# HomAlgDB contributor instructions

Read `docs/ARCHITECTURE.md` and `docs/IMPLEMENTATION.md` before changing tooling.
The implementation follows the approved HomAlgDB requirements, version 1.0
(2026-10-27). The source specification is currently available next to this
checkout as `../homalg-db-requirements-and-plan.md`.
The owner's 2026-10-28 amendment enables independent agent cross-review for
routine gates; follow `docs/REVIEW_POLICY.md` and the tracked review policy.

- Use English for code, identifiers, comments, repository documentation and commits.
- Preserve the document's definitions, hypotheses and proof route. Record Mathlib
  counterparts as metadata; do not substitute them for the source's construction.
- A node lives at `HomAlg/<DocKey>/<LocalId>.lean`, has id `<DocKey>.<LocalId>`,
  and declares its constants in `namespace <DocKey>`.
- Lean node headers are authored truth. Never put derived fields in them.
  Regenerate roots with `homalg gen-roots` and authored JSON with `homalg extract`.
- Do not rename merged node ids. Keep auxiliary, bridge and cited nodes distinct.
- Every remaining `sorry` belongs to a named theorem with a source and a natural
  language proof in its docstring. Do not introduce hollow definitions.
- Do not commit PDFs, page images, private transcriptions or local engine state.
  Scanned source transcription must use vision, never OCR.
- Real human confirmations, dispute resolutions and human fidelity reviews must
  only be written by their guarded human commands. Synthetic test records are
  explicitly fictional and confer no approval on a real document.
- Under the enabled policy, independent agents review foundations, first-chapter
  definitions and explained deviations, then continue through the normal gates.
  Record actual author/reviewer sessions and current evidence; escalate unresolved
  mathematical or source disagreements instead of inventing a satisfactory verdict.
- Formalization work stays inside its document and task scope. Infrastructure
  work and the two synthetic fixtures are maintained together during bootstrap.
- Never run a direct Lake build during an active Horizon run. Use `horizon check`
  or a command sharing its workspace lock. Bootstrap builds run without Horizon.
- Do not send issues or messages during a formalization run; use its local inbox.
- Add positive and negative tests for parser, schema and pipeline changes.
  Run `make test`, `make validate` and `make site` before reporting completion.
- Report implemented and pending milestone acceptance honestly. Context-dependent
  validation rules must report skipped coverage; unimplemented commands must not report success.
- Keep changes reviewable by task. PR descriptions use Summary, FR-NFR covered,
  How verified, and Not done & spec issues.
