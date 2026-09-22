"""Tests for HTML sunburst report generation."""

from pathlib import Path

from dss.cli import main
from dss.html_viz import render_html_report, write_html_report
from dss.scanner import scan


def test_render_html_contains_sunburst_and_tree(tmp_path: Path) -> None:
    (tmp_path / "big.bin").write_bytes(b"z" * 4096)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.bin").write_bytes(b"z" * 1024)

    result = scan(tmp_path)
    html = render_html_report(result)

    assert "<!DOCTYPE html>" in html
    assert "Circular sector" in html or "sector" in html
    assert "big.bin" in html
    assert '"kind": "file"' in html
    assert "application/json" in html


def test_write_html_and_cli(tmp_path: Path, capsys) -> None:
    (tmp_path / "f.dat").write_bytes(b"a" * 512)
    out = tmp_path / "report.html"
    result = scan(tmp_path)
    written = write_html_report(result, out, open_browser=False)
    assert written.exists()
    assert "Disk-Space-Scanner" in written.read_text(encoding="utf-8")

    report = tmp_path / "via-cli.html"
    assert main(["scan", str(tmp_path), "--html", str(report)]) == 0
    assert report.exists()
    err = capsys.readouterr().err
    assert "HTML report written" in err
