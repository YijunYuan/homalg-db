"""Regression cases for Lean lexical boundaries and header source locations."""

import pytest

from homalg.headers import HeaderError, code_only, imports_of, lex, parse_header

SAMPLE = """import Mathlib.Data.Nat.Basic

/-!
```yaml node
id: Fixture2000.Def_1
kind: definition
doc: Fixture2000
source: {label: "Definition 1", pages: [1]}
tags: [basic]
decls: []
fidelity: {status: faithful}
```

## Statement

A toy object.

## Description

A lexical fixture.
-/
"""


def test_header_sections_and_lines() -> None:
    """Keep authored prose and exact physical source line numbers."""
    header = parse_header(SAMPLE)
    assert header.line == 3
    assert header.yaml_line == 5
    assert header.section_lines["Statement"] == 14
    assert header.authored()["statement_md"] == "A toy object."
    assert header.metadata["source"]["pages"] == [1]
    assert imports_of(SAMPLE) == ["Mathlib.Data.Nat.Basic"]


def test_lexical_boundaries() -> None:
    """Comment markers in strings, characters and quoted names are inert."""
    source = "\n".join(
        [
            "/- outer /- inner -/ done -/",
            'def x := "escaped \\" /-! string -/"',
            'def y := r##"raw " /-! text -/"##',
            "def c := '\"'",
            "def x' := 1",
            "def «/-! name -/» := 1",
            "-- /-! ignored -/",
        ]
    )
    spans = lex(source)
    assert not [span for span in spans if span.kind == "moddoc"]
    assert "".join(source[a:b] for _, a, b in spans) == source
    assert len([span for span in spans if span.kind == "block"]) == 1
    assert code_only(source).count("\n") == source.count("\n")


@pytest.mark.parametrize(
    "source,line",
    [
        ("\n/- unclosed", 2),
        ('\n\n"unclosed', 3),
        ('r#"unclosed', 1),
        ("«unclosed", 1),
    ],
)
def test_unterminated_tokens(source: str, line: int) -> None:
    """Every unterminated lexical region reports its own starting line."""
    with pytest.raises(HeaderError) as caught:
        lex(source)
    assert caught.value.line == line


@pytest.mark.parametrize(
    "old,new,line",
    [
        ("id: Fixture2000.Def_1", "id:\tFixture2000.Def_1", 5),
        ("tags: [basic]", "tags: &tags [basic]", 9),
        ("tags: [basic]", "tags: !custom [basic]", 9),
        ("tags: [basic]", "tags: [basic]\ntags: [basic]", 10),
        ("A toy object.", "A /- nested -/ object.", 16),
        ("## Description", "## Statement", 18),
    ],
)
def test_malformed_headers(old: str, new: str, line: int) -> None:
    """Reject ambiguous YAML and forbidden header syntax with precise locations."""
    with pytest.raises(HeaderError) as caught:
        parse_header(SAMPLE.replace(old, new))
    assert caught.value.line == line


def test_header_must_precede_declarations() -> None:
    """A quoted fake comment does not hide an earlier declaration."""
    with pytest.raises(HeaderError, match="precede declarations"):
        parse_header('def x := "/-! fake -/"\n' + SAMPLE)


def test_markdown_fence_does_not_create_a_section() -> None:
    """Headings inside code examples are preserved as Markdown content."""
    source = SAMPLE.replace("A toy object.", "```text\n## Description\n```")
    assert parse_header(source).sections["Statement"] == "```text\n## Description\n```"


def test_import_text_inside_quoted_identifier_is_not_an_import() -> None:
    """Lean permits multiline quoted identifiers, which cannot supply dependencies."""
    source = "def «hello\nimport HomAlg.Fixture2000.Def_1\nworld» : Nat := 1"
    assert imports_of(source) == []


@pytest.mark.parametrize(
    "suffix",
    [
        'def x := s!"{"/-! fake -/"}"',
        'def x := s!"{"/-"}"',
        'def x := s!"{s!"{"nested"}"}"',
        'def x := s!"{let x := "}"; x}"',
        'def x := s!"{r#"/-"#}"',
    ],
)
def test_interpolated_strings_do_not_expose_fake_comments(suffix: str) -> None:
    """The nested expressions of standard interpolation stay inside one string span."""
    assert parse_header(SAMPLE + suffix).metadata["id"] == "Fixture2000.Def_1"
    assert len([span for span in lex(suffix) if span.kind == "moddoc"]) == 0
