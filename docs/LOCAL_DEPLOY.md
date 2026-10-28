# Local deployment

The built frontend runs either from static JSON or from a local SQLite service. Both modes use the same public record schemas and the same application routes.

Install the optional service dependencies and generate the public data:

```sh
uv sync --project tools --extra serve
make data
cd site && npm ci && npm run build
```

Serve the static build:

```sh
uv run --project tools --extra serve homalg serve --static site/dist
```

Open `http://127.0.0.1:8787/`. Serving through HTTP is required; opening the HTML file directly does not work.

For a database snapshot generated from `build/index.json`:

```sh
uv run --project tools homalg build-db
uv run --project tools --extra serve homalg serve \
  --static site/dist --db build/homalg.sqlite
```

Open `http://127.0.0.1:8787/?source=api`. To preserve prerendered layouts, highlighted Lean and other fields from an existing deployment, build from its data directory:

```sh
uv run --project tools homalg build-db --data site/dist/data
```

`build-db --from PATH --out PATH` selects another index or database destination. Database construction uses a temporary sibling file and atomically replaces the destination after all inserts succeed. An unsuccessful rebuild preserves the previous snapshot. Restart the service after replacing its database to make the transition explicit for open browser sessions.

The server binds to `127.0.0.1` by default. `--host` and `--port` configure the listening address. A Vite development frontend can use `http://localhost:5173/?source=api&api=http://127.0.0.1:8787`; loopback HTTP/HTTPS origins are permitted by CORS. Put runtime data-source options before the URL's `#` route.

The read-only API provides:

| Endpoint | Result |
| --- | --- |
| `/api/manifest` | Manifest with ETag revalidation |
| `/api/documents/{docKey}` | Complete document bundle |
| `/api/documents/{docKey}?chapter=` | Chapter overview with no node/edge payload |
| `/api/documents/{docKey}?chapter=1` | Chapter nodes, their outgoing edges and dependency stubs |
| `/api/nodes/{docKey}/{localId}` | Full node record |
| `/api/search` | Search results, facets and pagination |
| `/api/nodes/{docKey}/{localId}/neighbors?dir=up&depth=3` | Dependency edges; `down` follows dependents |
| `/api/taxonomy` | Tags, concepts and relations |
| `/api/global-graph` | Aggregated graph |
| `/api/global-dag?from=2000&to=2009` | A manifest-listed global DAG shard |
| `/api/evolution/{concept}` | Evolution record, or HTTP 404 when absent |
| `/api/health` | Public data-health findings |
| `/data/{path}` | Manifest-relative resources and downloads |

Search parameters are `q`, `doc`, `author`, `year`, `kind`, `headline`, `status`, `tags`, `concepts`, `fidelity`, `mathlib`, `aux`, `deps`, `dir`, `depth`, `sort` and `page`. Lists use commas; `year` accepts a year or inclusive range. `mathlib` and `aux` accept `yes` or `no`. Sort modes are `relevance`, `id`, `year` and `year-desc`. Pages contain 30 records. Full and local declaration identifiers use whole-token matching; ordinary text uses FTS5, prefix matching and vocabulary expansion. Tag filters include descendants.

Graph traversal runs through a recursive SQLite CTE, with depth 1–3 and at most 500 visited nodes including the origin. The edge-array response carries `X-Homalg-Truncated: true` when the cap excludes results. Dependency search excludes the origin and returns the same truncation flag in JSON. An empty `chapter` parameter requests the chapter overview; `chapter=__unsectioned__` selects nodes whose authored chapter is empty. Chapter requests avoid loading full document JSON and preserve references to dependencies in other chapters or documents.

Reproduce functional and performance checks:

```sh
uv run --project tools --extra serve pytest tools/tests/test_localdb.py
HOMALG_BENCHMARK=1 uv run --project tools --extra serve \
  pytest tools/tests/test_localdb_benchmark.py -q -s
```

The performance test constructs 100,000 explicitly synthetic nodes, generates their static artifacts, builds a SQLite database, and measures real FastAPI requests. It asserts search below 200 ms and a 1,000-node chapter response below one second across five warm requests. Measurements are written to `build/localdb-benchmark.json`; they describe the machine running the test. The contract suite compares fixture API payloads against static artifacts and checks ten queries against the actual browser MiniSearch implementation.
