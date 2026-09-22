"""Tests for tree building used by the sector visualization."""

from pathlib import Path

from dss.scanner import build_tree, scan


def _write(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_build_tree_files_are_own_sectors(tmp_path: Path) -> None:
    _write(tmp_path / "a.bin", 100)
    _write(tmp_path / "logs" / "app.log", 400)
    _write(tmp_path / "logs" / "debug.log", 200)

    result = scan(tmp_path)
    tree = build_tree(result)

    assert tree.kind == "dir"
    assert tree.size == 700

    kinds = {child.name: child.kind for child in tree.children}
    assert kinds["a.bin"] == "file"
    assert kinds["logs"] == "dir"

    logs = next(c for c in tree.children if c.name == "logs")
    file_names = sorted(c.name for c in logs.children)
    assert file_names == ["app.log", "debug.log"]
    assert all(c.kind == "file" for c in logs.children)
