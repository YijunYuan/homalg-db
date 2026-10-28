"""Lex Lean comments and read node headers without running Lean.

The segment interface follows SHEAF's leanindex.lex contract at 6e5abd8.
This is an independent implementation; see docs/IMPLEMENTATION.md for provenance.
Offsets are Python character offsets; diagnostics use one-based source lines.
"""

import re
from dataclasses import dataclass
from typing import Any, NamedTuple

from homalg.schemas import YamlError, load_yaml

SECTION_FIELDS = {
    "Statement": "statement_md",
    "Statement (original)": "statement_original_md",
    "Statement (corrected)": "statement_corrected_md",
    "Proof": "proof_md",
    "Description": "description_md",
    "Formalization notes": "notes_md",
    "History": "history_md",
}
THEOREM_KINDS = {"theorem", "lemma", "proposition", "corollary", "example", "exercise"}


class HeaderError(ValueError):
    """Malformed Lean or header syntax, retaining its source location."""

    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.line = line


class Segment(NamedTuple):
    """A half-open source span, compatible with leanindex.lex consumers."""

    kind: str
    start: int
    end: int


def _is_interpolated(text: str, start: int) -> bool:
    """Recognize standard interpolated-string introducers, including macro bang forms."""
    return bool(re.search(r"(?:\w+!|dbg_trace)\s*$", text[:start]))


def _string_end(text: str, start: int, interpolated: bool) -> int:
    """Scan a string and its nested interpolation expressions without exposing comments."""
    cursor = start + 1
    while cursor < len(text):
        if text[cursor] == "\\":
            cursor += 2
        elif text[cursor] == '"':
            return cursor + 1
        elif interpolated and text[cursor] == "{":
            cursor = _interpolation_end(text, cursor + 1, start)
        else:
            cursor += 1
    raise HeaderError("Unterminated string", text.count("\n", 0, start) + 1)


def _interpolation_end(text: str, cursor: int, origin: int) -> int:
    """Skip balanced expression braces, allowing comments and nested string literals."""
    depth = 1
    while cursor < len(text):
        if text.startswith("--", cursor):
            newline = text.find("\n", cursor)
            cursor = len(text) if newline < 0 else newline
        elif text.startswith("/-", cursor):
            comment_depth = 1
            cursor += 2
            while cursor < len(text) and comment_depth:
                if text.startswith("/-", cursor):
                    comment_depth += 1
                    cursor += 2
                elif text.startswith("-/", cursor):
                    comment_depth -= 1
                    cursor += 2
                else:
                    cursor += 1
        elif raw := re.match(r'r(#+)?"', text[cursor:]):
            terminator = '"' + (raw.group(1) or "")
            end = text.find(terminator, cursor + raw.end())
            cursor = len(text) if end < 0 else end + len(terminator)
        elif text[cursor] == '"':
            cursor = _string_end(text, cursor, _is_interpolated(text, cursor))
        elif text[cursor] == "«":
            end = text.find("»", cursor + 1)
            cursor = len(text) if end < 0 else end + 1
        elif text[cursor] == "'" and (
            literal := re.match(
                r"'(?:\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)|[^'\\\n])'", text[cursor:]
            )
        ):
            cursor += literal.end()
        else:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
                if depth == 0:
                    return cursor + 1
            cursor += 1
    raise HeaderError("Unterminated string interpolation", text.count("\n", 0, origin) + 1)


def lex(text: str) -> list[Segment]:
    """Recognize nested comments, escaped/raw strings, characters and quoted names."""
    spans: list[Segment] = []
    cursor = 0
    size = len(text)

    def error(message: str, offset: int) -> HeaderError:
        return HeaderError(message, text.count("\n", 0, offset) + 1)

    while cursor < size:
        start = cursor
        char = text[cursor]
        kind = "code"
        raw = re.match(r'r(#+)?"', text[cursor:]) if char == "r" else None
        if char.isspace():
            kind = "ws"
            while cursor < size and text[cursor].isspace():
                cursor += 1
        elif text.startswith("--", cursor):
            kind = "line"
            newline = text.find("\n", cursor)
            cursor = size if newline < 0 else newline
        elif text.startswith("/-", cursor):
            kind = (
                "moddoc"
                if text.startswith("/-!", cursor)
                else ("doc" if text.startswith("/--", cursor) else "block")
            )
            cursor += 2
            depth = 1
            while depth and cursor < size:
                if text.startswith("/-", cursor):
                    depth += 1
                    cursor += 2
                elif text.startswith("-/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise error("Unterminated block comment", start)
        elif raw:
            kind = "string"
            terminator = '"' + (raw.group(1) or "")
            end = text.find(terminator, cursor + raw.end())
            if end < 0:
                raise error("Unterminated raw string", start)
            cursor = end + len(terminator)
        elif char == '"':
            kind = "string"
            cursor = _string_end(text, cursor, _is_interpolated(text, cursor))
        elif char == "«":
            kind = "quoted_ident"
            end = text.find("»", cursor + 1)
            if end < 0:
                raise error("Unterminated quoted identifier", start)
            cursor = end + 1
        elif char == "'" and (
            cursor == 0 or not (text[cursor - 1].isalnum() or text[cursor - 1] in "_'!?")
        ):
            literal = re.match(
                r"'(?:\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)|[^'\\\n])'", text[cursor:]
            )
            if literal:
                kind = "char"
                cursor += literal.end()
            else:
                cursor += 1
        else:
            cursor += 1
        if spans and kind == "code" and spans[-1].kind == "code":
            previous = spans.pop()
            spans.append(Segment(kind, previous.start, cursor))
        else:
            spans.append(Segment(kind, start, cursor))
    return spans


def code_only(text: str) -> str:
    """Mask comments and literals, preserving offsets and line numbers."""
    return "".join(
        text[span.start : span.end]
        if span.kind in {"code", "ws"}
        else re.sub(r"[^\r\n]", " ", text[span.start : span.end])
        for span in lex(text)
    )


def imports_of(text: str) -> list[str]:
    """Read direct imports, excluding comments and string literals."""
    return sorted(set(re.findall(r"^\s*import\s+(\w+(?:\.\w+)*)", code_only(text), re.M)))


@dataclass(frozen=True)
class Header:
    """Parsed authored metadata and Markdown, with diagnostic locations."""

    metadata: dict[str, Any]
    sections: dict[str, str]
    line: int
    yaml_line: int
    section_lines: dict[str, int]
    start: int
    end: int

    def authored(self) -> dict[str, Any]:
        """Return the nodes-file authored record; absent sections remain absent."""
        return self.metadata | {
            SECTION_FIELDS[title]: content
            for title, content in self.sections.items()
            if title in SECTION_FIELDS
        }


def parse_header(text: str) -> Header:
    """Parse the first module comment, rejecting ambiguous or unsafe YAML headers."""
    spans = lex(text)
    comment = next((span for span in spans if span.kind == "moddoc"), None)
    if comment is None:
        raise HeaderError("Missing node module documentation comment")
    line = text.count("\n", 0, comment.start) + 1
    prefix = code_only(text[: comment.start])
    for index, source_line in enumerate(prefix.splitlines(), 1):
        if source_line.strip() and not re.fullmatch(
            r"\s*(?:prelude|import\s+\w+(?:\.\w+)*)(?:\s*)", source_line
        ):
            raise HeaderError("The node header must follow imports and precede declarations", index)
    body = text[comment.start + 3 : comment.end - 2]
    forbidden = re.search(r"/-|-/", body)
    if forbidden:
        raise HeaderError(
            "Comment delimiters are forbidden inside node headers",
            line + body.count("\n", 0, forbidden.start()),
        )
    lines = body.splitlines()
    first = next((index for index, value in enumerate(lines) if value.strip()), None)
    if first is None or lines[first].strip() != "```yaml node":
        raise HeaderError("The first header content must be a ```yaml node fence", line)
    closing = next((i for i in range(first + 1, len(lines)) if lines[i].strip() == "```"), None)
    if closing is None:
        raise HeaderError("Unclosed YAML node fence", line + first)
    yaml_text = "\n".join(lines[first + 1 : closing])
    yaml_line = line + first + 1
    if "\t" in yaml_text:
        raise HeaderError(
            "Tabs are forbidden in node YAML",
            yaml_line + yaml_text.count("\n", 0, yaml_text.index("\t")),
        )
    try:
        metadata = load_yaml(yaml_text)
    except YamlError as exc:
        raise HeaderError(str(exc), yaml_line + exc.line - 1) from exc
    if not isinstance(metadata, dict) or any(not isinstance(key, str) for key in metadata):
        raise HeaderError("Node YAML must be a mapping with string keys", yaml_line)
    sections: dict[str, str] = {}
    section_lines: dict[str, int] = {}
    current: str | None = None
    content: list[str] = []
    fence: str | None = None
    for index in range(closing + 1, len(lines)):
        value = lines[index]
        delimiter = re.match(r"^\s{0,3}(`{3,}|~{3,})", value)
        if delimiter:
            token = delimiter.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        heading = re.fullmatch(r"## (.+?)\s*", value) if fence is None else None
        if heading:
            if current is not None:
                sections[current] = "\n".join(content).strip()
            current = heading.group(1)
            if current in section_lines:
                raise HeaderError(f"Duplicate section: {current}", line + index)
            section_lines[current] = line + index
            content = []
        elif current is not None:
            content.append(value)
        elif value.strip():
            raise HeaderError("Expected a Markdown section after the YAML fence", line + index)
    if current is not None:
        sections[current] = "\n".join(content).strip()
    return Header(metadata, sections, line, yaml_line, section_lines, comment.start, comment.end)
