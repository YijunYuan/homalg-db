# Literature metadata and private sources

This directory contains public document metadata, claim records and generated
node metadata. The original sources for the two synthetic fixtures are in
`docs/fixtures/`; they require no PDF or claim.

Real PDFs, rendered page images, extracted text and complete transcriptions must
not be committed to the public repository. `make literature` clones or fast-forwards
the private repository named by `HOMALG_LITERATURE_REPO` or the ignored local file
`.homalg/literature-url`. No private URL is stored in public metadata.

`homalg literature add K --pdf FILE` verifies the registered SHA-256 and copies
the PDF into `literature/.private/K/`. Files over 50 MB require Git LFS. The ignored
`references` symlink exposes this checkout to Horizon. `homalg ingest-pdf K`
renders 200 dpi images, registers page anchors and extracts navigation text.
Transcribers read the page images, never the navigation text or OCR.

Use `homalg transcription land`, `review`, `status` and guarded `resolve` to track
exact page bytes. Changed reviewed files reopen automatically. Private page images
are ignored; PDF source files and reviewed TeX transcriptions can be backed up in
the private repository.

Third-party quotations retain their own copyright; see `NOTICE`.
