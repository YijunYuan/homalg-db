"""Corroborate a content-bound review with actual native Codex lifecycle records.

This is a cooperative execution audit, not a human signature or an OS sandbox.
Caller-supplied actor names and copied normalized text are never sufficient.
"""

import hashlib
import json
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any


def provider_root() -> Path:
    return Path.home() / ".codex/sessions"


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _records(path: Path, *, commands: bool = False) -> list[tuple[int, dict, str]]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Native execution evidence must be a regular file")
    result = []
    with path.open("rb") as stream:
        for number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except ValueError as exc:
                raise ValueError("Incomplete native execution evidence") from exc
            if not isinstance(value, dict):
                raise ValueError("Native execution evidence contains a non-object record")
            payload = value.get("payload", {})
            selected = value.get("kind") in {"session_meta", "subagent_start", "subagent_end"}
            selected |= commands and value.get("kind") in {"tool_call", "tool_result"}
            selected |= value.get("type") == "session_meta"
            selected |= value.get("type") == "event_msg" and payload.get("type") in {
                "task_started",
                "task_complete",
            }
            selected |= (
                commands
                and value.get("type") == "event_msg"
                and payload.get("type") == "item_completed"
            )
            selected |= (
                value.get("type") == "response_item"
                and payload.get("type") == "message"
                and payload.get("role") == "assistant"
            )
            if selected:
                # Keep only lifecycle and assistant evidence; large inherited
                # prompts/tool payloads are neither retained nor emitted.
                result.append((number, value, hashlib.sha256(line.rstrip(b"\r\n")).hexdigest()))
    return result


def completed_ack(
    repo: Path,
    owner: dict[str, Any],
    reference: dict[str, str],
    *,
    acknowledgement: dict[str, Any],
    not_before: str,
    forbidden_paths: set[str],
) -> dict[str, Any]:
    """Join the parent's observed child to its own fresh completed assistant turn."""
    return completed_turn(
        repo,
        owner,
        reference,
        acknowledgement=acknowledgement,
        not_before=not_before,
        forbidden_paths=forbidden_paths,
        role="source-fidelity-reviewer",
    )


def _event_child_id(data: dict[str, Any]) -> str | None:
    """Read supported opaque-ID fields, never a path/nickname or truthy fallback."""
    identities = [data[key] for key in ("subagent_thread_id", "subagent_key") if key in data]
    if not identities:
        return None
    if (
        any(
            not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value)
            for value in identities
        )
        or len(set(identities)) != 1
    ):
        raise ValueError("Native child ID aliases are invalid or contradictory")
    return identities[0]


def completed_turn(
    repo: Path,
    owner: dict[str, Any],
    reference: dict[str, str],
    *,
    acknowledgement: dict[str, Any] | None,
    not_before: str,
    forbidden_paths: set[str],
    role: str,
) -> dict[str, Any]:
    """Internal audit for a source reviewer or a historically collected node writer."""
    if role not in {"source-fidelity-reviewer", "node-writer"}:
        raise ValueError("Unsupported native evidence role")
    if set(reference) != {"child_id", "turn_id"} or not all(
        isinstance(value, str) and value for value in reference.values()
    ):
        raise ValueError("Review event requires exact child_id and turn_id")
    parent = repo / f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}"
    events = _records(parent / "transcript.jsonl")
    parent_ids = {
        event.get("data", {}).get("session_id")
        for _, event, _ in events
        if event.get("kind") == "session_meta"
        and not event.get("data", {}).get("subagent_thread_id")
        and event.get("data", {}).get("session_id")
    }
    if len(parent_ids) != 1:
        raise ValueError("Native parent execution identity is unavailable or ambiguous")
    parent_id = next(iter(parent_ids))
    starts = [
        row
        for row in events
        if row[1].get("kind") == "subagent_start"
        and row[1].get("data", {}).get("agent_role")
        and _event_child_id(row[1].get("data", {})) == reference["child_id"]
    ]
    if len(starts) != 1:
        raise ValueError("Expected one actual native reviewer dispatch")
    dispatch = starts[0]
    data = dispatch[1]["data"]
    actor = data.get("agent_path")
    if (
        data.get("parent_thread_id") != parent_id
        or data.get("agent_role") != role
        or actor in forbidden_paths
        or not isinstance(actor, str)
        or not actor.startswith("/root/")
    ):
        raise ValueError("Reviewer is not an independent native source reviewer")
    source = Path(data.get("source", ""))
    if (
        not source.is_absolute()
        or source != source.resolve()
        or not source.is_relative_to(provider_root().resolve())
        or any(part.is_symlink() for part in [source, *source.parents])
    ):
        raise ValueError("Reviewer evidence is not an actual provider session path")
    raw = _records(source)
    metas = [
        row
        for row in raw
        if row[1].get("type") == "session_meta"
        and row[1].get("payload", {}).get("id") == reference["child_id"]
    ]
    if len(metas) != 1:
        raise ValueError("Reviewer provider identity is unavailable or ambiguous")
    if metas[0] != next(row for row in raw if row[1].get("type") == "session_meta"):
        raise ValueError("Inherited provider identity cannot replace the actual child identity")
    meta = metas[0][1]["payload"]
    spawn = meta.get("source", {}).get("subagent", {}).get("thread_spawn", {})
    if (
        meta.get("parent_thread_id") != parent_id
        or meta.get("forked_from_id") != parent_id
        or meta.get("agent_path") != actor
        or meta.get("agent_role") != role
        or Path(meta.get("cwd", "")).resolve() != repo.resolve()
        or spawn.get("parent_thread_id") != parent_id
        or spawn.get("agent_path") != actor
        or spawn.get("agent_role") != role
        or spawn.get("depth") != 1
    ):
        raise ValueError("Reviewer provider lineage differs from the native dispatch")
    turns = [
        row
        for row in raw
        if row[1].get("type") == "event_msg"
        and row[1].get("payload", {}).get("type") == "task_started"
        and row[1]["payload"].get("turn_id") == reference["turn_id"]
    ]
    if len(turns) != 1:
        raise ValueError("Reviewer must identify one real started turn")
    start = turns[0]
    started = start[1]["payload"].get("started_at")
    if (
        type(started) is not int
        or started < int(_time(meta["timestamp"]).timestamp())
        or started < int(_time(not_before).timestamp())
        or _time(start[1]["timestamp"]) < _time(not_before)
        or start[0] <= metas[0][0]
        or reference["turn_id"] == start[1]["payload"].get("root_turn_id")
    ):
        raise ValueError("Inherited or pre-proposal reviewer turn cannot acknowledge this review")
    completions = [
        row
        for row in raw
        if row[1].get("type") == "event_msg"
        and row[1].get("payload", {}).get("type") == "task_complete"
        and row[1]["payload"].get("turn_id") == reference["turn_id"]
        and row[1]["payload"].get("started_at") == started
        and row[0] > start[0]
    ]
    if len(completions) != 1:
        raise ValueError("Reviewer must have one completed current turn")
    end = completions[0]
    message = end[1]["payload"].get("last_agent_message")
    if acknowledgement is not None:
        try:
            actual = json.loads(message)
        except (ValueError, TypeError) as exc:
            raise ValueError("Reviewer completion needs the exact JSON acknowledgement") from exc
        if actual != acknowledgement:
            raise ValueError("Reviewer acknowledged different proposal or assessment bytes")
    assistant = []
    for row in raw:
        value = row[1].get("payload", {})
        if (
            start[0] < row[0] < end[0]
            and row[1].get("type") == "response_item"
            and value.get("type") == "message"
            and value.get("role") == "assistant"
        ):
            text = "".join(
                item.get("text", "")
                for item in value.get("content", [])
                if item.get("type") in {"output_text", "text"}
            )
            if text == message:
                assistant.append(row)
    observed = [
        row
        for row in events
        if row[1].get("kind") == "subagent_end"
        and row[1]["data"].get("source") == str(source)
        and row[1]["data"].get("status") == "completed"
        and _time(row[1]["at"]) == _time(end[1]["timestamp"])
        and row[1]["data"].get("duration_seconds")
        == end[1]["payload"].get("duration_ms", -1) / 1000
        and _event_child_id(row[1]["data"]) == reference["child_id"]
    ]
    if (
        not assistant
        or len(observed) != 1
        or _time(end[1]["timestamp"]) < _time(start[1]["timestamp"])
    ):
        raise ValueError("Completion lacks actual assistant output or parent observation")
    return {
        "run": owner["run"],
        "parent_session": owner["session"],
        "parent_id": parent_id,
        "child_id": reference["child_id"],
        "turn_id": reference["turn_id"],
        "agent_path": actor,
        "role": role,
        "started_at": start[1]["timestamp"],
        "completed_at": end[1]["timestamp"],
        "evidence_sha256": {
            "session_meta": metas[0][2],
            "dispatch": dispatch[2],
            "start": start[2],
            "assistant": assistant[-1][2],
            "completion": end[2],
            "parent_observation": observed[0][2],
        },
    }


def parent_commit(
    repo: Path,
    owner: dict,
    commit: str,
    subject: str,
    *,
    not_before: str,
) -> dict:
    """Join one native lead's own completed commit command, excluding child copies."""
    parent = (
        repo / f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}/transcript.jsonl"
    )
    events = _records(parent, commands=True)
    identities = {
        row[1].get("data", {}).get("session_id")
        for row in events
        if row[1].get("kind") == "session_meta"
        and not row[1].get("data", {}).get("subagent_thread_id")
    }
    identities.discard(None)
    if len(identities) != 1:
        raise ValueError("Canonical integration requires one actual native lead identity")
    parent_id = next(iter(identities))
    if not re.fullmatch(r"[A-Za-z0-9-]+", parent_id):
        raise ValueError("Invalid native provider identity")
    paths = list(provider_root().rglob(f"*{parent_id}.jsonl"))
    if len(paths) != 1 or paths[0].resolve() != paths[0]:
        raise ValueError("Original native lead provider evidence unavailable or ambiguous")
    raw = _records(paths[0], commands=True)
    meta = next(row for row in raw if row[1].get("type") == "session_meta")
    if (
        meta[1]["payload"].get("id") != parent_id
        or meta[1]["payload"].get("parent_thread_id")
        or (
            isinstance(meta[1]["payload"].get("source"), dict)
            and meta[1]["payload"]["source"].get("subagent")
        )
        or Path(meta[1]["payload"].get("cwd", "")).resolve() != repo
    ):
        raise ValueError("Inherited child execution cannot attest a canonical lead amendment")
    matches = []
    for row in raw:
        payload = row[1].get("payload", {})
        item = payload.get("item", {})
        output = item.get("aggregated_output", "")
        summary = re.findall(r"(?m)^\[[^\]\n]+ ([0-9a-f]{7,40})\] (.+)$", output)
        command = item.get("command")
        if not (
            payload.get("type") == "item_completed"
            and item.get("type") == "CommandExecution"
            and payload.get("thread_id") == parent_id
            and item.get("status") == "completed"
            and item.get("exit_code") == 0
            and isinstance(command, list)
            and all(isinstance(word, str) for word in command)
            and any(commit.startswith(short) and title == subject for short, title in summary)
        ):
            continue
        if not re.search(r'"?\$HORIZON_GIT"?\s+commit\b', " ".join(command)):
            continue
        starts = [
            entry
            for entry in raw
            if entry[1].get("payload", {}).get("type") == "task_started"
            and entry[1]["payload"].get("turn_id") == payload.get("turn_id")
            and meta[0] < entry[0] < row[0]
        ]
        if (
            len(starts) != 1
            or item.get("cwd") != repo.as_uri()
            or type(payload.get("started_at_ms")) is not int
            or payload["started_at_ms"] < _time(not_before).timestamp() * 1000
            or payload.get("completed_at_ms", 0) < payload["started_at_ms"]
            or starts[0][1]["payload"].get("started_at", 0)
            < int(_time(meta[1]["payload"]["timestamp"]).timestamp())
        ):
            continue
        pairs = []
        for first, second in zip(events, events[1:], strict=False):
            left, right = first[1], second[1]
            if (
                left.get("kind") == "tool_call"
                and right.get("kind") == "tool_result"
                and left.get("tool") == right.get("tool") == "Bash"
                and not any(
                    key in event.get("data", {})
                    for event in (left, right)
                    for key in ("subagent_thread_id", "agent_path", "source")
                )
                and left.get("data") == {"command": shlex.join(command)}
                and right.get("data") == {"content": output, "exit_code": 0}
            ):
                pairs.append((first, second))
        if len(pairs) != 1:
            continue
        matches.append(
            {
                "run": owner["run"],
                "session": owner["session"],
                "parent_id": parent_id,
                "actor": "/root",
                "role": "native-lead",
                "turn_id": payload["turn_id"],
                "item_id": item["id"],
                "commit": commit,
                "evidence_sha256": {
                    "session_meta": meta[2],
                    "start": starts[0][2],
                    "command": row[2],
                    "observed_call": pairs[0][0][2],
                    "observed_result": pairs[0][1][2],
                },
            }
        )
    if len(matches) != 1:
        raise ValueError("Canonical amendment lacks one joined actual native lead commit execution")
    return matches[0]
