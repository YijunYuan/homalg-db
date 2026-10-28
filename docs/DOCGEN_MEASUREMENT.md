# Optional doc-gen4 measurement

The optional doc-gen4 integration remains **disabled**. The bounded local cold
documentation build on 2026-10-28 did not complete: GNU `timeout` returned **124**
at its configured 1,800-second limit. No complete website was produced.
This is a local WSL2 result, **not a measurement of GitHub Actions runtime**.
The CI 30-minute gate and the complete 500,000,000-byte artifact gate remain
unverified; the attempt does not establish a size-limit failure.

## Source and tool pins

| Input | Exact revision |
|---|---|
| Accepted HomAlg source ([PR #16](https://github.com/YijunYuan/homalg-db/pull/16)) | `5b4771d924974ea59a9c4c1ec5bd5713af4e6482` |
| Source tree | `5191e51f2a4f27301fc395290ef53f95d97ac164` |
| Lean toolchain | `leanprover/lean4:v4.35.0` |
| Mathlib | `56a005855ea17e0b0958f73ec801ae140b0a1679` |
| [doc-gen4 v4.35.0](https://github.com/leanprover/doc-gen4/tree/0e1ffe2e4ba5ecfdfaf15c65b8d3805dbb7134ae) | `0e1ffe2e4ba5ecfdfaf15c65b8d3805dbb7134ae` |

The isolated directory retained its preparatory PR label `homalg-e4b0cd6`, but
its actual Git HEAD was changed to the accepted main commit **before** the
measurement. The preparatory PR commit `e4b0cd6c8bc7b85e6a02903292d003855cfbcf85`
has the identical source tree. The [accepted-source record](measurements/docgen4-5b4771d-cold/accepted-source.json)
preserves this transition. The [documentation manifest](measurements/docgen4-5b4771d-cold/docbuild-manifest.json)
pins every transitive dependency; the production Lake graph was not changed.

## Environment and cache state

The runner was Linux 6.18.40.1-microsoft-standard-WSL2, an Intel Core i7-12700,
20 logical CPUs, and 24,032 MiB RAM. `LEAN_NUM_THREADS=4` was set. Available
memory and CPU details are retained in the [measurement record](measurements/docgen4-5b4771d-cold/measurement.json).
During preparation, observed machine I/O wait was about 10–11%; this local
storage behavior must not be extrapolated to a GitHub-hosted runner.

This was **cold documentation with prepared dependency/tool caches**, not a
fresh toolchain installation. Independent copies of pinned dependency sources,
compiled Mathlib/dependency caches, and the prepared doc-gen4 tool were used.
No HomAlg build cache, HTML output, `doc-data`, or documentation SQLite database
was copied. The script rejected preexisting documentation artifacts. These were
ordinary independent file copies (`cp -a --reflink=auto`), not writable symlinks
or hardlinks back to production.

Preparation is separate from the documentation timer:

- The initial isolated tool build was interrupted at the parent's request after
  63.79 seconds so pilot acceptance could proceed; it was not counted as a
  failed documentation measurement. Its authorized resume took 49.24 seconds
  and successfully completed all 194 tool jobs; the executable's `--help` worked.
- The isolated source/dependency-cache copy and pinned `lake update doc-gen4`
  setup took **1032.652 seconds**. Network/cache setup commands and
  their output are retained separately. The large copy cost is not hidden in a
  claimed CI build time.
- A preflight check initially rejected Lean's quoted manifest spelling
  `«doc-gen4»`. Recognition was corrected before any documentation build started;
  this was not classified as a budget failure.

## Command and result

The [docbuild configuration](measurements/docgen4-5b4771d-cold/docbuild-lakefile.toml)
used the official nested-package arrangement: SHA-pinned doc-gen4 and the
unchanged parent `homalg` package. Setup used
`MATHLIB_NO_CACHE_ON_UPDATE=1 LEAN_NUM_THREADS=4 lake update doc-gen4`.

The exact measured command, run from the isolated checkout's `docbuild/`, was:

```sh
LEAN_NUM_THREADS=4 /usr/bin/time -v \
  -o /home/yijunyuan/homalg-docgen-benchmark/measurement-5b4771d-cold/resources.txt \
  timeout --foreground --signal=TERM --kill-after=30 1800 \
  lake build HomAlg:docs
```

The [executed measurement script](measurements/docgen4-5b4771d-cold/measure-script.py.txt)
records the exact wrapper argv and initial state. It also checks the **actual
`doc/` tree**, every five seconds, for more than 500,000,000 bytes and terminates
only the isolated build process group on a limit. Dependency caches, `doc-data`
and the SQLite database are excluded from website-size accounting.
The timeout ended this attempt; no warm retry or extended build followed.

| Observation | Actual result |
|---|---|
| Exit status | `124` (configured timeout) |
| Python monotonic build duration | `1800.111056` seconds |
| GNU time reported elapsed duration | `30:49.73` |
| GNU time reported maximum RSS | `2,987,776` KiB |
| Last completed Lake progress | `6354/6705` jobs |
| Error lines / failed-job markers in retained log | `0` |
| Analyzed modules / declarations at stop | `4,446` / `189,147` |
| HTML directory at stop | Present but empty; `0` emitted website bytes |
| Complete website size | **Unknown**, not a successful zero-byte artifact |
| Declaration inventory and representative HTML link | Not generated / not verifiable without completed HTML |
| Production Lake manifest and lakefile | Byte-for-byte unchanged |
| Isolated accepted tracked source | Unchanged |
| Remaining processes in this build's process group | None after cleanup |

The two raw elapsed-time readings disagree by about 49.6 seconds. Both are
preserved rather than silently substituting one for the other; the clock
discrepancy was not independently diagnosed. The monotonic watchdog and GNU
timeout both used the configured 1,800-second bound. Neither reading is evidence
of a successful CI run. The GNU time RSS figure is its reported process statistic,
not a measurement of aggregate concurrent-system memory.

At interruption, temporary documentation working files occupied
`301,307,606` bytes; that number is **not** a website size.
The log contains nonfatal module-system, linter and optional equational-lemma
warnings, but no `error:` line or failed-job marker before the timeout.
The source was not altered to omit expensive imports or target a smaller library.
The normal `HomAlg:docs` facet includes imported modules and doc-gen4's core
Lean/Init/Std/Lake documentation.

## Evidence and decision

The small raw evidence is tracked in
[`docs/measurements/docgen4-5b4771d-cold/`](measurements/docgen4-5b4771d-cold/),
with a complete [SHA256SUMS](measurements/docgen4-5b4771d-cold/SHA256SUMS).
Key SHA-256 digests are:

| Artifact | SHA-256 |
|---|---|
| [Complete build log](measurements/docgen4-5b4771d-cold/build.txt) | `da36abb43ae2869673c766446a06fa2b877e89e591fbaa935e7259838ec41f9e` |
| [Measurement JSON](measurements/docgen4-5b4771d-cold/measurement.json) | `98ccb1e6397de078a23186dd9eadcd1a19bb571e0ff0f134f2cc779e91b3227c` |
| [Resource log](measurements/docgen4-5b4771d-cold/resources.txt) | `a2ef2d08c75a5b24b7c158b434c1239041d3ad9167d9c1a2957a52bccf1ec59a` |
| [Executed wrapper](measurements/docgen4-5b4771d-cold/measure-script.py.txt) | `8c64963577e0a1098daf3ae607338188ae323e1f8717a0d76bb5d3ed268494ce` |

Original local evidence remains under
`/home/yijunyuan/homalg-docgen-benchmark/measurement-5b4771d-cold/`; isolated
working files remain under
`/home/yijunyuan/homalg-docgen-benchmark/homalg-e4b0cd6/docbuild/.lake/build/`.
The large temporary database and dependency cache are not published.

No weekly `docs.yml`, documentation Release assets, restored `site/dist/docs/`,
or declaration-page links were enabled. M7-T7's optional enablement criteria
have not been demonstrated. A future attempt would need a successful complete
build on a representative CI runner, the complete artifact byte count,
`decls.txt` from that same successful build, a verified declaration target, and
the deployment's combined size-budget check before publication is enabled.
