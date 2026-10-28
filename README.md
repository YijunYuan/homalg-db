# HomAlgDB

A Lean 4 database of the homological-algebra literature. Each document keeps its
own definitions and proof route, with one metadata-bearing Lean file per node.
The [public site](https://yijunyuan.github.io/homalg-db/) exposes dependencies,
source fidelity, search and concept history.

The implementation includes the Lean exporter and validation pipeline, a React
site, collaboration commands, private PDF ingestion and a local Horizon fork.
Two original synthetic documents exercise 17 Lean nodes. The Hochschild 1945
pilot has reviewed visual transcriptions and is undergoing formal proof and fidelity review. See [implementation status](docs/IMPLEMENTATION.md)
for acceptance evidence and remaining work.

## Quick start

Prerequisites: Git, Python 3.12+, uv, Node.js 22+ with npm, and elan. Run from this
checkout. The first Lake command downloads the pinned Lean/Mathlib dependencies.

```sh
make setup
lake exe cache get
make test
make validate
make data
make site
```

Python and npm dependencies are locked in `tools/uv.lock` and
`site/package-lock.json`. Lean and Mathlib are pinned to v4.35.0, with resolved
Git revisions recorded in `lake-manifest.json`. Normal installs use the lockfiles.

```sh
uv run --project tools --locked homalg --help
uv run --project tools --locked homalg validate --fast --json
uv run --project tools --locked homalg gen-roots
uv run --project tools --locked homalg extract --doc Fixture2000
uv run --project tools --locked homalg export-lean --doc Fixture2000
python3 -m http.server 8080 --directory site/dist
```

The exporter emits compiled JSON facts, including direct/transitive `sorry`,
dependency evidence, axiom closure and statement hashes. `extract` preserves
derived records; `export-lean` refreshes them. Validation reports context-dependent
checks under `summary.skipped`: for example, PR ownership needs PR context and
private source provenance needs the private literature checkout.

See [site development](docs/SITE.md), [local serving](docs/LOCAL_DEPLOY.md), and
[contributor workflow](docs/CONTRIBUTING.md). Optional dependencies are installed
by `make setup`; individual installations can select `--extra ingest`,
`--extra serve` or `--extra evolution`.

## Contributing

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md),
[conventions](docs/CONVENTIONS.md) and [CI/governance](docs/CI.md).
Run `make test`, `make validate`, and `make site` before submitting changes.
Never commit PDFs, page images, private transcriptions or engine state.

Governance tooling previews changes offline by default. No GitHub repository,
Pages deployment or remote governance configuration is created by local setup.

```sh
make governance GOVERNANCE_ARGS='--repository OWNER/homalg-db'
```

Code uses [Apache-2.0](LICENSE). Original prose and data use
[CC BY 4.0](LICENSE-DATA). Third-party quotations are excluded; see [NOTICE](NOTICE).
