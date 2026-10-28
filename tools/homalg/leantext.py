"""Conservative source-command analysis for validation and statement context locks.

This reader understands the project's conventional Lean layout, not arbitrary
user-defined command syntax. Compilation remains authoritative for declarations.
"""

import hashlib
import re
from dataclasses import dataclass

from homalg.headers import code_only, lex

DECL_KINDS = {
    "def",
    "abbrev",
    "theorem",
    "lemma",
    "structure",
    "class",
    "inductive",
    "instance",
    "opaque",
    "axiom",
    "example",
}
MODIFIERS = r"(?:(?:private|protected|noncomputable|nonrec|unsafe|partial|local|scoped|public)\s+)*"
DECLARATION = re.compile(
    rf"^(?P<modifiers>{MODIFIERS})(?P<kind>{'|'.join(sorted(DECL_KINDS))})\b\s*"
)
OTHER = re.compile(
    r"^(?:(?:local|scoped)\s+)?(?:variable|universe|open|notation|infix[lr]?|prefix|postfix|macro|syntax|elab|attribute|set_option|include|omit)\b"
)


@dataclass(frozen=True)
class Command:
    """A conventional Lean command with retained source spans and active statement context."""

    kind: str
    name: str
    raw_name: str
    namespace: str
    modifiers: str
    text: str
    statement: str
    context: tuple[str, ...]
    docstring: str
    start: int
    end: int
    line: int


def strip_comments(text: str) -> str:
    """Remove comments without removing literals or quoted declaration identifiers."""
    return "".join(
        re.sub(r"[^\n]", " ", text[start:end])
        if kind in {"line", "block", "doc", "moddoc"}
        else text[start:end]
        for kind, start, end in lex(text)
    )


def without_attributes(text: str) -> str:
    """Remove balanced attribute annotations while preserving declaration modifiers."""
    masked = code_only(text)
    ranges = []
    cursor = 0
    while (start := masked.find("@[", cursor)) >= 0:
        depth = 1
        end = start + 2
        while end < len(masked) and depth:
            depth += (masked[end] == "[") - (masked[end] == "]")
            end += 1
        ranges.append((start, end))
        cursor = end
    for start, end in reversed(ranges):
        text = text[:start] + " " * (end - start) + text[end:]
    return text


def statement_end(text: str) -> int:
    """Find a declaration body's separator, ignoring binder defaults and quoted text."""
    masked = code_only(text)
    depth = 0
    cursor = 0
    while cursor < len(masked):
        char = masked[cursor]
        if char in "([{⦃":
            depth += 1
        elif char in ")]}⦄":
            depth = max(depth - 1, 0)
        if depth == 0 and (
            masked.startswith(":=", cursor) or re.match(r"\bwhere\b", masked[cursor:])
        ):
            return cursor
        cursor += 1
    return len(text)


def commands(text: str) -> list[Command]:
    """Read commands, tracking namespace/section lifetime and one-command contexts."""
    stripped = strip_comments(text)
    masked = code_only(text)
    offsets = []
    offset = 0
    for line in masked.splitlines(keepends=True):
        candidate = without_attributes(line).strip()
        if (
            DECLARATION.match(candidate)
            or OTHER.match(candidate)
            or re.match(
                r"^(?:namespace|(?:noncomputable\s+)?section|end|import|prelude)\b", candidate
            )
        ):
            offsets.append(offset + len(line) - len(line.lstrip()))
        offset += len(line)
    # Attribute-only lines and docstrings attach to the next declaration by lookup.
    scopes: list[tuple[str, str, list[str]]] = [("root", "", [])]
    pending: list[str] = []
    output: list[Command] = []
    docspans = [(start, end) for kind, start, end in lex(text) if kind == "doc"]
    for position, start in enumerate(offsets):
        end = offsets[position + 1] if position + 1 < len(offsets) else len(text)
        body = without_attributes(stripped[start:end]).strip()
        first = body.splitlines()[0] if body else ""
        namespace = ".".join(name for kind, name, _ in scopes if kind == "namespace")
        if match := re.match(r"namespace\s+(\S+)", first):
            scopes.append(("namespace", match.group(1), []))
            continue
        if re.match(r"(?:noncomputable\s+)?section\b", first):
            scopes.append(("section", "", []))
            continue
        if re.match(r"end\b", first):
            if len(scopes) > 1:
                scopes.pop()
            continue
        if re.match(r"(?:import|prelude)\b", first):
            continue
        match = DECLARATION.match(body)
        context = tuple(command for _, _, active in scopes for command in active) + tuple(pending)
        if match:
            kind, modifiers = match["kind"], match["modifiers"].strip()
            rest = body[match.end() :]
            name_match = re.match(r"([^\s({\[:⦃]+)", rest)
            raw_name = name_match.group(1) if name_match and kind != "example" else ""
            if kind == "instance" and (not raw_name or rest.startswith((":", "(", "[", "{"))):
                raw_name = ""
            name = raw_name.removeprefix("_root_.")
            if name and namespace and not raw_name.startswith("_root_."):
                name = f"{namespace}.{name}"
            statement = (
                body[: statement_end(body)].strip()
                if kind in {"theorem", "lemma", "axiom", "example"}
                else body
            )
            docstring = ""
            for doc_start, doc_end in reversed(docspans):
                if doc_end <= start and not without_attributes(masked[doc_end:start]).strip():
                    docstring = text[doc_start + 3 : doc_end - 2].strip()
                    break
            output.append(
                Command(
                    kind,
                    name,
                    raw_name,
                    namespace,
                    modifiers,
                    body,
                    statement,
                    context,
                    docstring,
                    start,
                    end,
                    text.count("\n", 0, start) + 1,
                )
            )
            pending = []
        else:
            # `... in` applies to one declaration only, and must not leak to its sibling.
            if re.match(r"(?:open|set_option)\b", first) and re.search(r"\bin\s*$", first):
                pending.append(body)
            elif OTHER.match(first):
                scopes[-1][2].append(body)
            output.append(
                Command(
                    "other",
                    "",
                    "",
                    namespace,
                    "",
                    body,
                    body,
                    context,
                    "",
                    start,
                    end,
                    text.count("\n", 0, start) + 1,
                )
            )
    return output


def statement_hashes(text: str) -> dict[str, str]:
    """Hash interfaces and contexts; proof edits leave theorem locks intact."""
    return {
        command.name: hashlib.sha256(
            " ".join("\n".join((*command.context, command.statement)).split()).encode()
        ).hexdigest()
        for command in commands(text)
        if command.name
    }


def sorry_count(text: str) -> int:
    """Count actual sorry/admit tokens, ignoring comments, strings and quoted names."""
    return len(re.findall(r"(?<![\w.'])(?:sorry|admit)(?![\w'])", code_only(text)))
