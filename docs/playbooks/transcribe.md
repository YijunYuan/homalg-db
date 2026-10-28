# Transcribe and review scanned pages

Run `homalg ingest-pdf <DocKey>` after `make literature`. It verifies the PDF hash,
renders 200 dpi page images and records navigation text without OCR. The image is
the transcription source. Text-layer extraction under `text/` is only for finding
pages; never use it or OCR as transcription content.

Dispatch a vision-capable page transcriber for at most five PDF pages. Read
`references/<DocKey>/pages/page-NNNN.png`; PDF indices differ from printed pages
according to `document.yaml.pdf.page_offset`. If an image is unreadable, report
the problem. A higher-resolution render of the same PDF can resolve tiny symbols.

Write each private `references/<DocKey>/tex/page-NNNN.tex` with `% source:`,
`% pdf_page:`, `% retrieved:` and `% transcribed_by:` comments. Then include any
necessary local macro declarations and the faithful LaTeX body. Prefer standard
LaTeX commands; document-specific conventions may require expanded macros.
Preserve theorem numbers, Fraktur letters, formulas and printed mistakes. Remove
running headers, printed page numbers and download footers. Place footnotes at
the page end as `[Footnote n]` paragraphs. Keep each fragment of a cross-page
sentence on its own page. Mark unreadable text `% [illegible]` without guessing.

```sh
homalg transcription land Hochschild1945 --pages 2-6 \
  --session "$ARCHON_HORIZON_SESSION" --engine codex
```

Include `--model` only when its exact identity is known. Landing records the
delivered byte hashes and marks the pages transcribed. Assign another reviewer
to compare every page image with those bytes: signs, indices, exponents,
inequalities, quantifiers, delimiters, footnotes and cross-page joins.

```sh
homalg transcription review Hochschild1945 --pages 2-6 --status mismatch \
  --by independent-review-session \
  --finding 'symbol: page-0003 equation (1): error: The printed congruence is an equals sign in the transcription.'
```

Use `satisfactory` only after a complete comparison. `partial`, `mismatch` and
`unverified` retain the transcribed state. Fix the reported differences, land
again and review again. `needs-adjudication` marks a page disputed and requests a
human decision; only a human can use `transcription resolve`. Agents must not
invoke that command or edit the disputed state manually. The user override dated
2026-10-28 permits independent agent fidelity/foundation reviews but explicitly
retains human decisions for unresolved disputes, including disputed pages.

```sh
homalg transcription status Hochschild1945 --json
```

Only reviewed bytes may feed inventory and node excerpts. Editing a reviewed
file makes its previous review stale. The private snapshot/after-session hooks
enforce the T task's page scope and handle private commits/push retries. PDFs,
page images, whole-page transcriptions and the private repository URL never enter
the public repository or static site.
