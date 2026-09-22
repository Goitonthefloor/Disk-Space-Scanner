"""Tests for filesystem scanning."""

from pathlib import Path

from dss.scanner import scan, top_directories


def _write(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_scan_totals_and_large_files(tmp_path: Path) -> None:
    _write(tmp_path / "a.bin", 100)
    _write(tmp_path / "sub" / "b.bin", 250)
    _write(tmp_path / "sub" / "c.bin", 50)

    result = scan(tmp_path, min_size=100)

    assert result.file_count == 3
    assert result.total_size == 400
    assert result.dir_sizes[tmp_path] == 400
    assert result.dir_sizes[tmp_path / "sub"] == 300
    assert [entry.size for entry in result.large_files] == [250, 100]


def test_top_directories(tmp_path: Path) -> None:
    _write(tmp_path / "logs" / "app.log", 800)
    _write(tmp_path / "cache" / "obj", 200)
    _write(tmp_path / "cache" / "nested" / "obj2", 100)

    result = scan(tmp_path)
    tops = top_directories(result, limit=2)

    assert tops[0].path == tmp_path / "logs"
    assert tops[0].size == 800
    assert tops[1].path == tmp_path / "cache"
    assert tops[1].size == 300


def test_skips_symlinks_by_default(tmp_path: Path) -> None:
    target = tmp_path / "real.bin"
    _write(target, 120)
    link = tmp_path / "link.bin"
    link.symlink_to(target)

    result = scan(tmp_path, min_size=0)
    assert result.file_count == 1
    assert result.total_size == 120
