"""CLI smoke tests."""

import json
from pathlib import Path

from dss.cli import main


def test_scan_text_and_json(tmp_path: Path, capsys) -> None:
    big = tmp_path / "big.bin"
    big.write_bytes(b"y" * 2048)

    assert main(["scan", str(tmp_path), "--min-size", "1KB", "--top", "5"]) == 0
    out = capsys.readouterr().out
    assert "Disk-Space-Scanner" in out
    assert "big.bin" in out

    assert main(["scan", str(tmp_path), "--json", "--min-size", "1KB"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["file_count"] == 1
    assert data["top_files"][0]["path"].endswith("big.bin")


def test_invalid_size_exits_2(capsys) -> None:
    assert main(["scan", ".", "--min-size", "nope"]) == 2
    err = capsys.readouterr().err
    assert "Invalid size" in err or "error:" in err
