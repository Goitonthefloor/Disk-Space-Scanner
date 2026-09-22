"""Filesystem walk and aggregation for disk space analysis."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, order=True)
class FileEntry:
    size: int
    path: Path


@dataclass
class ScanResult:
    root: Path
    total_size: int = 0
    file_count: int = 0
    dir_count: int = 0
    large_files: list[FileEntry] = field(default_factory=list)
    dir_sizes: dict[Path, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    disk_total: int | None = None
    disk_used: int | None = None
    disk_free: int | None = None


def _collect_disk_usage(path: Path, result: ScanResult) -> None:
    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        result.errors.append(f"disk usage unavailable for {path}: {exc}")
        return
    result.disk_total = usage.total
    result.disk_used = usage.used
    result.disk_free = usage.free


def scan(
    root: Path,
    *,
    min_size: int = 0,
    follow_symlinks: bool = False,
) -> ScanResult:
    """Walk ``root`` and collect size statistics.

    Analysis only — never deletes or moves files.
    """
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    result = ScanResult(root=root)
    _collect_disk_usage(root, result)

    # Accumulate sizes bottom-up via a dict keyed by path.
    dir_sizes: dict[Path, int] = {root: 0}

    for dirpath, dirnames, filenames in os.walk(
        root,
        topdown=True,
        followlinks=follow_symlinks,
        onerror=lambda err: result.errors.append(str(err)),
    ):
        current = Path(dirpath)
        result.dir_count += 1
        if current not in dir_sizes:
            dir_sizes[current] = 0

        # Skip descending into symlinked dirs unless explicitly following.
        if not follow_symlinks:
            dirnames[:] = [
                name
                for name in dirnames
                if not (current / name).is_symlink()
            ]

        for name in filenames:
            path = current / name
            try:
                if path.is_symlink() and not follow_symlinks:
                    continue
                st = path.lstat() if not follow_symlinks else path.stat()
            except OSError as exc:
                result.errors.append(f"{path}: {exc}")
                continue

            size = int(st.st_size)
            result.file_count += 1
            result.total_size += size
            dir_sizes[current] = dir_sizes.get(current, 0) + size

            if size >= min_size:
                result.large_files.append(FileEntry(size=size, path=path))

    # Bubble each directory's size into its immediate parent (deepest first).
    for path in sorted(dir_sizes.keys(), key=lambda p: len(p.parts), reverse=True):
        if path == root:
            continue
        parent = path.parent
        dir_sizes[parent] = dir_sizes.get(parent, 0) + dir_sizes[path]

    result.dir_sizes = dir_sizes
    result.large_files.sort(reverse=True)
    return result


def top_directories(result: ScanResult, *, limit: int, max_depth: int | None = 2) -> list[FileEntry]:
    """Return the largest directories limited by depth relative to the scan root."""
    root_depth = len(result.root.parts)
    entries: list[FileEntry] = []
    for path, size in result.dir_sizes.items():
        if path == result.root or size <= 0:
            continue
        rel_depth = len(path.parts) - root_depth
        if max_depth is not None and rel_depth > max_depth:
            continue
        entries.append(FileEntry(size=size, path=path))
    entries.sort(reverse=True)
    return entries[:limit]
