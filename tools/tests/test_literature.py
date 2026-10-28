"""Real PDF rendering and private transcription lifecycle regression coverage."""

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from homalg.cli import cli
from homalg.documents import dump_metadata
from homalg.human import HumanApprovalRequired
from homalg.literature import add_pdf, file_hash, ingest_pdf, page_range
from homalg.scaffold import new_document_files
from homalg.schemas import load_yaml
from homalg.transcription import land, review, status


@pytest.fixture
def private_document(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    """Create a tiny authored PDF; never use third-party source in public tests."""
    pymupdf = pytest.importorskip("pymupdf")
    pdf = pymupdf.open()
    for number in range(1, 4):
        page = pdf.new_page(width=144, height=144)
        page.insert_text((12, 24), f"Original test page {number}.")
    source = tmp_path / "private-test.pdf"
    pdf.save(source)
    pdf.close()
    files = new_document_files(repo, "Private2002", source, title="Original private test")
    for relative, text in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    root = repo / "literature/.private"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    add_pdf(repo, "Private2002", source)
    tex = root / "Private2002/tex"
    tex.mkdir()
    for number in range(1, 4):
        (tex / f"page-{number:04}.tex").write_text(
            f"% source: Private2002/private-test.pdf\n% pdf_page: {number}\n"
            "% retrieved: 2026-10-28\n% transcribed_by: fixture-vision\n"
            f"Original test page {number}.\n"
        )
    return repo, source


def test_ingestion_checks_identity_and_renders_pdf_indices(
    private_document: tuple[Path, Path],
) -> None:
    """Hash verification precedes rendering and page image geometry matches 200 dpi."""
    import pymupdf

    repo, source = private_document
    result = ingest_pdf(repo, "Private2002", pages="2")
    assert result["rendered_pages"] == [2]
    assert result["sha256"] == file_hash(source)
    assert result["page_characters"]["0002"] > 0
    image = repo / "references/Private2002/pages/page-0002.png"
    pixmap = pymupdf.Pixmap(image)
    assert (pixmap.width, pixmap.height) == (400, 400)
    assert not (image.parent / "page-0001.png").exists()
    assert (repo / "literature/Private2002/text/page-0002.txt").exists()
    manifest = load_yaml((repo / "literature/.private/manifest.yaml").read_text())
    assert manifest["references"][0]["slug"] == "Private2002"
    assert "PDF index" in manifest["references"][0]["read"]
    source.write_bytes(b"changed source")
    with pytest.raises(ValueError, match="SHA-256"):
        add_pdf(repo, "Private2002", source)


def test_page_review_reopens_changed_bytes(private_document: tuple[Path, Path]) -> None:
    """A successful review cannot approve later source edits, even when an old review remains."""
    repo, _ = private_document
    land(repo, "Private2002", pages="1-2", session="writer")
    review(repo, "Private2002", pages="1-2", verdict="satisfactory", by="reviewer")
    assert status(repo, "Private2002")["counts"]["reviewed"] == 2
    page = repo / "references/Private2002/tex/page-0001.tex"
    page.write_text(page.read_text() + "A changed formula.\n")
    view = status(repo, "Private2002")
    assert view["changed_after_review"] == ["0001"]
    assert view["counts"]["transcribed"] == 1
    with pytest.raises(ValueError, match="changed since landing"):
        review(repo, "Private2002", pages="1", verdict="satisfactory", by="reviewer")
    land(repo, "Private2002", pages="1", session="writer-two")
    review(repo, "Private2002", pages="1", verdict="partial", by="reviewer-two")
    assert status(repo, "Private2002")["pages"]["0001"]["status"] == "transcribed"


def test_transcriber_cannot_review_own_session(private_document: tuple[Path, Path]) -> None:
    """Independent review evidence must not reuse the transcribing session identity."""
    repo, _ = private_document
    land(repo, "Private2002", pages="1", session="writer")
    with pytest.raises(ValueError, match="different reviewer"):
        review(repo, "Private2002", pages="1", verdict="satisfactory", by="writer")
    assert status(repo, "Private2002")["counts"]["reviewed"] == 0


def test_disputed_transcription_cannot_be_silently_cleared(
    private_document: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Agent landing/reviews cannot replace the explicitly required human adjudication."""
    repo, _ = private_document
    land(repo, "Private2002", pages="1", session="writer")
    monkeypatch.setattr(
        "homalg.engine.horizon",
        lambda *a, **kw: "I-0001",
    )
    review(repo, "Private2002", pages="1", verdict="needs-adjudication", by="reviewer")
    with pytest.raises(ValueError, match="human resolution"):
        land(repo, "Private2002", pages="1", session="writer")
    with pytest.raises(ValueError, match="Only a human"):
        review(repo, "Private2002", pages="1", verdict="satisfactory", by="reviewer")
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "agent")
    with pytest.raises(HumanApprovalRequired):
        review(
            repo,
            "Private2002",
            pages="1",
            verdict="satisfactory",
            by="human",
            human=True,
            note="Inspected the page",
        )
    assert status(repo, "Private2002")["pages"]["0001"]["status"] == "disputed"


def test_wrong_pdf_metadata_and_provenance_refuse_writes(
    private_document: tuple[Path, Path],
) -> None:
    """Metadata identity, filename safety and page provenance are checked before landing."""
    repo, _ = private_document
    page = repo / "references/Private2002/tex/page-0001.tex"
    page.write_text(page.read_text().replace("pdf_page: 1", "pdf_page: 2"))
    with pytest.raises(ValueError, match="does not match"):
        land(repo, "Private2002", pages="1", session="writer")
    assert not (repo / "references/Private2002/transcription.yaml").exists()
    path = repo / "literature/Private2002/document.yaml"
    data = load_yaml(path.read_text())
    data["pdf"]["file"] = "../escape.pdf"
    path.write_text(dump_metadata(data))
    with pytest.raises(ValueError, match="plain filename"):
        ingest_pdf(repo, "Private2002")


@pytest.mark.parametrize("value", ["0", "4", "2-1", "-1", "1-", "1,,2", "../2"])
def test_bad_pdf_ranges(value: str) -> None:
    """Invalid ranges cannot address files outside registered PDF pages."""
    with pytest.raises(ValueError):
        page_range(value, 3)


def test_cli_transcription_report_is_one_json(private_document: tuple[Path, Path]) -> None:
    """The nested command retains common report semantics and repo options."""
    repo, _ = private_document
    result = CliRunner().invoke(
        cli, ["transcription", "status", "Private2002", "--repo", str(repo), "--json"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["counts"]["todo"] == 3
