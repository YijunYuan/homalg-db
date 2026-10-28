"""Atomic SQLite snapshots with indexed facets, FTS5 and bounded recursive graph queries."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from homalg.relations import merged_ids
from homalg.repository import DOC_KEY
from homalg.retired import resolve_retired, retirement_map

DB_VERSION = 1
PAGE_SIZE = 30
MAX_NEIGHBORS = 500
FACETS = (
    "headline",
    "doc",
    "author",
    "year",
    "kind",
    "status",
    "tags",
    "concepts",
    "fidelity",
    "mathlib",
    "aux",
)
TEXT_FIELDS = (
    "title",
    "label",
    "id",
    "statement_text",
    "description_text",
    "tags",
    "concepts",
    "decl_names",
    "doc_title",
    "authors",
)
SCHEMA = """
PRAGMA user_version=1;
CREATE TABLE resources(path TEXT PRIMARY KEY, payload TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE documents(doc TEXT PRIMARY KEY,base TEXT NOT NULL,bundle TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE nodes(rowid INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, doc TEXT NOT NULL,
 chapter TEXT NOT NULL, year INTEGER NOT NULL, kind TEXT NOT NULL, headline TEXT,
 status TEXT NOT NULL, fidelity TEXT NOT NULL, has_mathlib INTEGER NOT NULL,
 is_aux INTEGER NOT NULL, summary TEXT NOT NULL, record TEXT NOT NULL, search TEXT NOT NULL);
CREATE INDEX nodes_doc_chapter ON nodes(doc,chapter);
CREATE INDEX nodes_year ON nodes(year,id);
CREATE TABLE layouts(node TEXT PRIMARY KEY,payload TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE facets(node INTEGER NOT NULL, facet TEXT NOT NULL, value TEXT NOT NULL,
 PRIMARY KEY(node,facet,value)) WITHOUT ROWID;
CREATE INDEX facets_value ON facets(facet,value,node);
CREATE TABLE identifiers(node INTEGER NOT NULL,token TEXT NOT NULL,
 PRIMARY KEY(node,token)) WITHOUT ROWID;
CREATE INDEX identifiers_token ON identifiers(token,node);
CREATE TABLE edges(source TEXT NOT NULL,target TEXT NOT NULL,payload TEXT NOT NULL,
 PRIMARY KEY(source,target)) WITHOUT ROWID;
CREATE INDEX edges_target ON edges(target,source);
CREATE VIRTUAL TABLE search_fts USING fts5(title,label,id,statement_text,description_text,
 tags,concepts,decl_names,doc_title,authors, tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE search_vocabulary USING fts5vocab(search_fts,'row');
CREATE TABLE terms(term TEXT PRIMARY KEY,initial TEXT NOT NULL,size INTEGER NOT NULL) WITHOUT ROWID;
CREATE INDEX terms_initial_size ON terms(initial,size);
CREATE INDEX terms_size ON terms(size);
"""


def compact(value: Any) -> str:
    """Keep large immutable payloads compact without losing Unicode or key order stability."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def facet_values(record: dict) -> dict[str, list[str]]:
    """Use exactly the public search facet names and representations."""
    return {
        "headline": [record["headline"]] if record["headline"] else [],
        "doc": [record["doc"]],
        "author": record["authors"],
        "year": [str(record["year"])],
        "kind": [record["kind"]],
        "status": [record["status"]],
        "tags": record["tags"],
        "concepts": record["concepts"],
        "fidelity": [record["fidelity"]],
        "mathlib": ["yes" if record["has_mathlib"] else "no"],
        "aux": ["yes" if record["is_aux"] else "no"],
    }


def build_artifacts_db(artifacts: dict[str, Any], out: Path) -> dict[str, Any]:
    """Index an existing static snapshot and atomically replace the completed database."""
    manifest = artifacts["manifest.json"]
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported manifest schema version")
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    node_count = 0
    totals: dict[str, Counter] = {key: Counter() for key in FACETS}
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;" + SCHEMA)
        for path, payload in sorted(artifacts.items()):
            if path.startswith(("nodes/", "documents/", "search/", "search-index.")):
                continue
            connection.execute("INSERT INTO resources VALUES (?,?)", (path, compact(payload)))
        for entry in manifest["documents"]:
            doc = entry["doc_key"]
            bundle = artifacts[entry["files"]["document"]]
            base = {
                key: value
                for key, value in bundle.items()
                if key not in {"nodes", "edges", "external_nodes", "layout"}
            }
            if bundle.get("layout"):
                base["layout"] = {
                    key: value for key, value in bundle["layout"].items() if key != "nodes"
                } | {"nodes": {}}
                connection.executemany(
                    "INSERT OR IGNORE INTO layouts VALUES (?,?)",
                    (
                        (identifier, compact(point))
                        for identifier, point in bundle["layout"]["nodes"].items()
                    ),
                )
            elif "layout" in bundle:
                base["layout"] = None
            connection.execute(
                "INSERT INTO documents VALUES (?,?,?)", (doc, compact(base), compact(bundle))
            )
            summaries = {node["id"]: node for node in bundle["nodes"]}
            for record in artifacts[entry["files"]["search_shard"]]:
                node_count += 1
                identifier = record["id"]
                full = artifacts[f"nodes/{doc}/{record['local_id']}.json"]
                summary = summaries[identifier]
                connection.execute(
                    "INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        node_count,
                        identifier,
                        doc,
                        record["chapter"],
                        record["year"],
                        record["kind"],
                        record["headline"],
                        record["status"],
                        record["fidelity"],
                        int(record["has_mathlib"]),
                        int(record["is_aux"]),
                        compact(summary),
                        compact(full),
                        compact(record),
                    ),
                )
                whole = set()
                for field in ("id", "label", "decl_names"):
                    value = (
                        " ".join(record[field])
                        if isinstance(record[field], list)
                        else record[field]
                    )
                    for token in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[._][A-Za-z0-9]+)+", value):
                        whole.update((token.casefold(), token.rsplit(".", 1)[-1].casefold()))
                connection.executemany(
                    "INSERT INTO identifiers VALUES (?,?)",
                    ((node_count, token) for token in sorted(whole)),
                )
                values = facet_values(record)
                connection.executemany(
                    "INSERT INTO facets VALUES (?,?,?)",
                    (
                        (node_count, field, value)
                        for field, items in values.items()
                        for value in set(items)
                    ),
                )
                for field, items in values.items():
                    totals[field].update(set(items))
                text = [
                    " ".join(record[field])
                    if isinstance(record[field], list)
                    else str(record[field])
                    for field in TEXT_FIELDS
                ]
                connection.execute("INSERT INTO search_fts VALUES (?,?,?,?,?,?,?,?,?,?)", text)
            connection.executemany(
                "INSERT INTO edges VALUES (?,?,?)",
                ((edge["from"], edge["to"], compact(edge)) for edge in bundle["edges"]),
            )
        connection.execute("INSERT INTO resources VALUES (?,?)", ("__facets", compact(totals)))
        connection.execute(
            "INSERT INTO terms SELECT term,substr(term,1,1),length(term) FROM search_vocabulary"
        )
        connection.execute("INSERT INTO search_fts(search_fts) VALUES('optimize')")
        connection.commit()
        connection.execute("ANALYZE")
        connection.commit()
        connection.close()
        temporary.chmod(0o644)
        os.replace(temporary, out)
    finally:
        connection.close()
        temporary.unlink(missing_ok=True)
    return {
        "file": str(out),
        "documents": len(manifest["documents"]),
        "nodes": node_count,
        "bytes": out.stat().st_size,
    }


def build_db(
    repo: Path, out: Path | None = None, *, source: Path | None = None, data: Path | None = None
) -> dict[str, Any]:
    """Build from index.json or preserve every byte-level field of a prerendered static snapshot."""
    out = out or repo / "build/homalg.sqlite"
    if data is not None:
        artifacts = {
            path.relative_to(data).as_posix(): json.loads(path.read_text())
            for path in data.rglob("*.json")
            if not path.name.startswith("search-index.")
        }
    else:
        from homalg.schemas import SchemaStore
        from homalg.sitedata import build_site_data

        source = source or repo / "build/index.json"
        index = json.loads(source.read_text())
        errors = SchemaStore(repo / "schema").validate(index, "index.schema.json")
        if errors:
            raise ValueError(f"Invalid index: {errors[0].message}")
        sources = {
            node["id"]: (repo / node["derived"]["file"]["path"]).read_text()
            for node in index["nodes"]
        }
        artifacts = build_site_data(index, sources)
    return build_artifacts_db(artifacts, out)


class Database:
    """Read an immutable snapshot through short-lived, thread-safe connections."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        if not self.path.is_file():
            raise ValueError(f"Database does not exist: {path}")
        with self.connect() as connection:
            if connection.execute("PRAGMA user_version").fetchone()[0] != DB_VERSION:
                raise ValueError("Unsupported HomAlgDB database version; rebuild the database")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(f"file:{quote(str(self.path))}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _resource(connection: sqlite3.Connection, name: str) -> Any:
        row = connection.execute("SELECT payload FROM resources WHERE path=?", (name,)).fetchone()
        if row is None:
            raise KeyError(name)
        return json.loads(row[0])

    def resource(self, name: str) -> Any:
        with self.connect() as connection:
            try:
                return self._resource(connection, name)
            except KeyError:
                manifest = self._resource(connection, "manifest.json")
                for entry in manifest["documents"]:
                    if name == entry["files"]["document"]:
                        return self.document(entry["doc_key"])
                    if name == entry["files"]["search_shard"]:
                        return [
                            json.loads(row[0])
                            for row in connection.execute(
                                "SELECT search FROM nodes WHERE doc=? ORDER BY id",
                                (entry["doc_key"],),
                            )
                        ]
                match = re.fullmatch(r"nodes/([^/]+)/([^/]+)\.json", name)
                if match:
                    return self.node(f"{match[1]}.{match[2]}")
                raise

    def _resolve_node(self, connection: sqlite3.Connection, identifier: str) -> str:
        """Resolve historical identities from this immutable snapshot's manifest."""
        manifest = self._resource(connection, "manifest.json")
        target = resolve_retired(identifier, retirement_map(manifest.get("retired", [])))
        if target is None:
            raise KeyError(identifier)
        return target

    def node(self, identifier: str) -> dict:
        with self.connect() as connection:
            identifier = self._resolve_node(connection, identifier)
            row = connection.execute(
                "SELECT record FROM nodes WHERE id=?", (identifier,)
            ).fetchone()
            if row is None:
                raise KeyError(identifier)
            return json.loads(row[0])

    def document(self, key: str, chapter: str | None = None) -> dict:
        with self.connect() as connection:
            column = "bundle" if chapter is None else "base"
            row = connection.execute(
                f"SELECT {column} FROM documents WHERE doc=?", (key,)
            ).fetchone()
            if row is None:
                raise KeyError(key)
            if chapter is None:
                return json.loads(row["bundle"])
            base = json.loads(row["base"])
            if chapter == "":
                return base | {"nodes": [], "edges": [], "external_nodes": []}
            if chapter == "__unsectioned__":
                chapter = ""
            base["chapters"] = [item for item in base["chapters"] if item["chapter"] == chapter]
            if not base["chapters"]:
                raise KeyError(f"{key} chapter {chapter}")
            rows = connection.execute(
                "SELECT id,summary FROM nodes WHERE doc=? AND chapter=? ORDER BY id", (key, chapter)
            ).fetchall()
            base["nodes"] = [json.loads(item["summary"]) for item in rows]
            base["edges"] = [
                json.loads(item[0])
                for item in connection.execute(
                    "SELECT e.payload FROM edges e JOIN nodes n ON n.id=e.source "
                    "WHERE n.doc=? AND n.chapter=? ORDER BY e.source,e.target",
                    (key, chapter),
                )
            ]
            ids = {item["id"] for item in rows}
            external = sorted({edge["to"] for edge in base["edges"]} - ids)
            base["external_nodes"] = []
            for identifier in external:
                ref = connection.execute(
                    "SELECT summary FROM nodes WHERE id=?", (identifier,)
                ).fetchone()
                if ref is None:
                    raise ValueError(f"Dangling dependency in database: {identifier}")
                summary = json.loads(ref[0])
                base["external_nodes"].append(
                    {
                        field: summary[field]
                        for field in ("id", "label", "headline", "status", "doc")
                    }
                )
            if base.get("layout"):
                for identifier in sorted(ids | set(external)):
                    point = connection.execute(
                        "SELECT payload FROM layouts WHERE node=?", (identifier,)
                    ).fetchone()
                    if point:
                        base["layout"]["nodes"][identifier] = json.loads(point[0])
            return base

    @staticmethod
    def _neighbors(
        connection: sqlite3.Connection, identifier: str, direction: str, depth: int
    ) -> tuple[list[dict], bool]:
        if direction not in {"up", "down"} or not 1 <= depth <= 3:
            raise ValueError("Neighbors require dir=up|down and depth=1..3")
        if not connection.execute("SELECT 1 FROM nodes WHERE id=?", (identifier,)).fetchone():
            raise KeyError(identifier)
        origin, target = ("source", "target") if direction == "up" else ("target", "source")
        # Breadth-first recursive CTE, limited in the recursion itself. DISTINCT on
        # (id,level) avoids exponential duplicate paths in layered dependency DAGs.
        rows = connection.execute(
            f"""WITH RECURSIVE walk(id,level) AS (
            SELECT ?,0 UNION SELECT e.{target},walk.level+1 FROM edges e
            JOIN walk ON e.{origin}=walk.id WHERE walk.level<?
            ORDER BY 2,1 LIMIT ?)
            SELECT id,min(level) AS level FROM walk GROUP BY id ORDER BY level,id""",
            (identifier, depth, MAX_NEIGHBORS * (depth + 1) + 1),
        ).fetchall()
        chosen = rows[:MAX_NEIGHBORS]
        truncated = len(rows) > MAX_NEIGHBORS
        ids = {row["id"] for row in chosen}
        frontier = [row["id"] for row in chosen if row["level"] < depth]
        if not frontier:
            return [], truncated
        marks = ",".join("?" for _ in frontier)
        edges = connection.execute(
            f"SELECT source,target,payload FROM edges WHERE {origin} IN ({marks}) "
            f"ORDER BY {origin},{target}",
            frontier,
        )
        output = []
        for edge in edges:
            if edge[target] in ids:
                output.append(json.loads(edge["payload"]))
            else:
                truncated = True
        return output, truncated

    def neighbors(
        self, identifier: str, direction: str = "up", depth: int = 1
    ) -> tuple[list[dict], bool]:
        with self.connect() as connection:
            return self._neighbors(
                connection, self._resolve_node(connection, identifier), direction, depth
            )

    def global_dag(self, first: int, last: int) -> dict:
        if first > last:
            raise ValueError("Global DAG start year must not exceed its end year")
        manifest = self.resource("manifest.json")
        shards = [
            self.resource(entry["file"])
            for entry in manifest["global_dag_files"]
            if entry["to"] >= first and entry["from"] <= last
        ]
        nodes = {
            node["id"]: node
            for shard in shards
            for node in shard["nodes"]
            if first <= node["year"] <= last
        }
        edges = {
            compact(edge): edge
            for shard in shards
            for edge in shard["edges"]
            if edge["from"] in nodes and edge["to"] in nodes
        }
        return {
            "range": [first, last],
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
        }

    @staticmethod
    def _distance(left: str, right: str, maximum: int) -> int:
        """Bounded edit distance for FTS vocabulary expansion, never SQL interpolation."""
        if abs(len(left) - len(right)) > maximum:
            return maximum + 1
        row = list(range(len(right) + 1))
        for i, char in enumerate(left, 1):
            current = [i]
            for j, other in enumerate(right, 1):
                current.append(min(current[-1] + 1, row[j] + 1, row[j - 1] + (char != other)))
            if min(current) > maximum:
                return maximum + 1
            row = current
        return row[-1]

    @classmethod
    def _match(cls, connection: sqlite3.Connection, text: str) -> str | None:
        exact = bool(re.search(r"[A-Za-z][A-Za-z0-9]*(?:[._][A-Za-z0-9]+)+", text))
        if exact:
            # A quoted FTS phrase preserves numeric identifier components, so
            # Thm_1 cannot match Thm_10 and untrusted punctuation is never syntax.
            return " AND ".join('"' + token.replace('"', '""') + '"' for token in text.split())
        terms = re.findall(r"[^\W_]+", text.casefold())
        if not terms:
            return None
        expressions = []
        for term in terms[:32]:
            alternatives = ['"' + term.replace('"', '""') + '"*']
            maximum = min(2, len(term) // 5)
            if maximum:
                candidates = connection.execute(
                    "SELECT term FROM terms WHERE size BETWEEN ? AND ? "
                    "AND term GLOB '[a-z]*' LIMIT 4000",
                    (len(term) - maximum, len(term) + maximum),
                )
                for candidate in candidates:
                    word = candidate[0]
                    if word != term and cls._distance(term, word, maximum) <= maximum:
                        alternatives.append('"' + word.replace('"', '""') + '"')
            expressions.append("(" + " OR ".join(alternatives) + ")")
        return " AND ".join(expressions)

    @staticmethod
    def _query(query: dict[str, Any]) -> dict[str, Any]:
        """Validate URL parameter names and bounded ranges before executing SQL."""
        fields = set(FACETS) - {"year"} | {"q", "year", "deps", "dir", "depth", "sort", "page"}
        if unknown := set(query) - fields:
            raise ValueError("Unknown search parameters: " + ", ".join(sorted(unknown)))
        values = {key: value for key, value in query.items() if value is not None and value != ""}
        for name in ("q", *FACETS, "deps"):
            if name in values and (not isinstance(values[name], str) or len(values[name]) > 2048):
                raise ValueError(f"Invalid {name} search parameter")
        for name in ("mathlib", "aux"):
            if name in values and values[name] not in {"yes", "no"}:
                raise ValueError(f"{name} must be yes or no")
        if values.get("sort", "relevance") not in {"relevance", "id", "year", "year-desc"}:
            raise ValueError("sort must be relevance, id, year or year-desc")
        if values.get("dir", "down") not in {"up", "down"}:
            raise ValueError("dir must be up or down")
        try:
            values["page"] = int(values.get("page", 1))
            values["depth"] = int(values.get("depth", 1))
        except (ValueError, TypeError) as error:
            raise ValueError("page and depth must be integers") from error
        if not 1 <= values["page"] <= 1000000 or not 1 <= values["depth"] <= 3:
            raise ValueError("page must be positive and depth must be between 1 and 3")
        if "year" in values and not re.fullmatch(r"\d{1,4}(?:-\d{1,4})?", values["year"]):
            raise ValueError("year must be a year or inclusive year range")
        if "deps" in values:
            parts = values["deps"].split(".")
            if (
                len(parts) != 2
                or not DOC_KEY.fullmatch(parts[0])
                or not re.fullmatch(r"[A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*", parts[1])
            ):
                raise ValueError("deps must be a valid node id")
        return values

    def search(self, query: dict[str, Any]) -> dict:
        """FTS text, parameterized facets, dependency closure and stable 30-row pagination."""
        query = self._query(query)
        with self.connect() as connection:
            conditions, parameters = [], []
            text = query.get("q", "").strip()
            match = self._match(connection, text) if text else None
            joined, score = "", "0.0"
            if text:
                if match is None:
                    conditions.append("0")
                else:
                    joined = " JOIN search_fts ON search_fts.rowid=n.rowid"
                    score = (
                        "bm25(search_fts,3,3,2,1,1,2,2,2,1,1)"
                        if query.get("sort", "relevance") == "relevance"
                        else "0.0"
                    )
                    conditions.append("search_fts MATCH ?")
                    parameters.append(match)
                    for token in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:[._][A-Za-z0-9]+)+", text):
                        conditions.append(
                            "EXISTS (SELECT 1 FROM identifiers i "
                            "WHERE i.node=n.rowid AND i.token=?)"
                        )
                        parameters.append(token.casefold())
            scalar = {
                "doc": "doc",
                "kind": "kind",
                "headline": "headline",
                "status": "status",
                "fidelity": "fidelity",
            }
            for field, column in scalar.items():
                if query.get(field):
                    values = [value for value in query[field].split(",") if value]
                    conditions.append(f"n.{column} IN ({','.join('?' for _ in values)})")
                    parameters.extend(values)
            for field in ("author", "tags", "concepts"):
                if query.get(field):
                    values = set(query[field].split(",")) - {""}
                    if field in {"tags", "concepts"}:
                        aliases = merged_ids(self._resource(connection, "taxonomy.json")[field])
                        values = {aliases.get(value, value) for value in values}
                    if field == "tags":
                        tags = self._resource(connection, "taxonomy.json")["tags"]
                        previous = set()
                        while previous != values:
                            previous = values.copy()
                            values.update(tag["id"] for tag in tags if tag.get("parent") in values)
                    conditions.append(
                        "EXISTS (SELECT 1 FROM facets f WHERE f.node=n.rowid AND f.facet=? "
                        f"AND f.value IN ({','.join('?' for _ in values)}))"
                    )
                    parameters.extend([field, *sorted(values)])
            if "year" in query:
                bounds = list(map(int, query["year"].split("-")))
                first, last = bounds[0], bounds[-1]
                if first > last:
                    raise ValueError("The start of a year range must not exceed its end")
                conditions.append("n.year BETWEEN ? AND ?")
                parameters.extend((first, last))
            for field, column in (("mathlib", "has_mathlib"), ("aux", "is_aux")):
                if field in query:
                    conditions.append(f"n.{column}=?")
                    parameters.append(int(query[field] == "yes"))
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            connection.execute(
                "CREATE TEMP TABLE matched(node INTEGER PRIMARY KEY, score REAL NOT NULL)"
            )
            connection.execute(
                f"INSERT INTO matched SELECT n.rowid,{score} FROM nodes n{joined}{where}",
                parameters,
            )
            total_before_graph = connection.execute("SELECT count(*) FROM matched").fetchone()[0]
            total_nodes = connection.execute("SELECT count(*) FROM nodes").fetchone()[0]
            # Facets match the static worker, which computes them before applying
            # the capped dependency filter. Reuse exact totals for an all-node hit.
            if total_before_graph == total_nodes:
                facets = self._resource(connection, "__facets")
            else:
                facets = {key: {} for key in FACETS}
                for row in connection.execute(
                    "SELECT f.facet,f.value,count(*) FROM matched m CROSS JOIN facets f "
                    "ON f.node=m.node GROUP BY f.facet,f.value"
                ):
                    facets[row[0]][row[1]] = row[2]
            truncated = False
            if query.get("deps"):
                query["deps"] = self._resolve_node(connection, query["deps"])
                edges, truncated = self._neighbors(
                    connection, query["deps"], query.get("dir", "down"), query["depth"]
                )
                ids = {node for edge in edges for node in (edge["from"], edge["to"])} - {
                    query["deps"]
                }
                if ids:
                    connection.execute(
                        "DELETE FROM matched WHERE node NOT IN (SELECT rowid FROM nodes "
                        f"WHERE id IN ({','.join('?' for _ in ids)}))",
                        sorted(ids),
                    )
                else:
                    connection.execute("DELETE FROM matched")
            total = connection.execute("SELECT count(*) FROM matched").fetchone()[0]
            ordering = {
                "id": "n.id",
                "year": "n.year,n.id",
                "year-desc": "n.year DESC,n.id",
                "relevance": "m.score,n.year,n.id",
            }[query.get("sort", "relevance")]
            records = [
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT n.search FROM matched m JOIN nodes n ON n.rowid=m.node "
                    f"ORDER BY {ordering} LIMIT ? OFFSET ?",
                    (PAGE_SIZE, (query["page"] - 1) * PAGE_SIZE),
                )
            ]
            return {
                "records": records,
                "total": total,
                "page": query["page"],
                "page_size": PAGE_SIZE,
                "facets": facets,
                "truncated": truncated,
            }
