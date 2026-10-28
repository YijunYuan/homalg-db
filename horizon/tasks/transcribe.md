Visually transcribe PDF pages {pages} of {doc_title} ({doc_key}).

Write scope: {write_scope}. Read the rendered images in references/{doc_key}/pages/.
Dispatch page-transcriber with a vision-capable model, preferably {transcriber_model},
at most five consecutive pages per dispatch. Never read text/ or use OCR as a source.
Keep every formula, quantifier, sign, subscript, condition and footnote; retain the
source's notation. Unreadable text stays marked % [illegible]. Include the required
source/pdf_page/retrieved/transcribed_by headers and only this page's LaTeX macros.

Land the files with homalg transcription land {doc_key} --pages <range> --session
"$ARCHON_HORIZON_SESSION". Dispatch a separate transcription-fidelity-reviewer
to compare the images and delivered files. Record its five-level verdict with
homalg transcription review. An ambiguous source requires human adjudication;
do not resolve it or modify human evidence yourself.

Done when homalg stage-check {task_id} exits 0. Then set this task to done.
