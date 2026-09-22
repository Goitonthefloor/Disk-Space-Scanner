"""Human-readable and JSON report formatting."""

from __future__ import annotations

import json
from typing import Any

from .scanner import ScanResult, top_directories
from .sizes import format_size


def build_report_data(
    result: ScanResult,
    *,
    top: int,
    dir_top: int,
    min_size: int,
) -> dict[str, Any]:
    large = result.large_files[:top]
    dirs = top_directories(result, limit=dir_top)
    data: dict[str, Any] = {
        "root": str(result.root),
        "total_size": result.total_size,
        "total_size_human": format_size(result.total_size),
        "file_count": result.file_count,
        "dir_count": result.dir_count,
        "min_size": min_size,
        "min_size_human": format_size(min_size),
        "disk": {
            "total": result.disk_total,
            "used": result.disk_used,
            "free": result.disk_free,
            "total_human": format_size(result.disk_total or 0) if result.disk_total is not None else None,
            "used_human": format_size(result.disk_used or 0) if result.disk_used is not None else None,
            "free_human": format_size(result.disk_free or 0) if result.disk_free is not None else None,
        },
        "top_files": [
            {"path": str(entry.path), "size": entry.size, "size_human": format_size(entry.size)}
            for entry in large
        ],
        "top_directories": [
            {"path": str(entry.path), "size": entry.size, "size_human": format_size(entry.size)}
            for entry in dirs
        ],
        "errors": list(result.errors),
    }
    return data


def format_text_report(
    result: ScanResult,
    *,
    top: int,
    dir_top: int,
    min_size: int,
) -> str:
    data = build_report_data(result, top=top, dir_top=dir_top, min_size=min_size)
    lines: list[str] = []
    lines.append(f"Disk-Space-Scanner — {data['root']}")
    lines.append("=" * max(40, len(lines[0])))
    lines.append("")
    lines.append("Overview")
    lines.append(f"  Total scanned : {data['total_size_human']} ({data['file_count']} files, {data['dir_count']} dirs)")
    if data["disk"]["total"] is not None:
        lines.append(
            f"  Mount usage   : {data['disk']['used_human']} used / "
            f"{data['disk']['free_human']} free / {data['disk']['total_human']} total"
        )
    lines.append(f"  Min file size : {data['min_size_human']}")
    lines.append("")

    lines.append(f"Largest directories (top {dir_top})")
    if not data["top_directories"]:
        lines.append("  (none)")
    else:
        for entry in data["top_directories"]:
            lines.append(f"  {entry['size_human']:>10}  {entry['path']}")
    lines.append("")

    lines.append(f"Largest files (top {top}, ≥ {data['min_size_human']})")
    if not data["top_files"]:
        lines.append("  (none)")
    else:
        for entry in data["top_files"]:
            lines.append(f"  {entry['size_human']:>10}  {entry['path']}")

    if data["errors"]:
        lines.append("")
        lines.append(f"Warnings ({len(data['errors'])})")
        for err in data["errors"][:20]:
            lines.append(f"  ! {err}")
        if len(data["errors"]) > 20:
            lines.append(f"  … and {len(data['errors']) - 20} more")

    lines.append("")
    return "\n".join(lines)


def format_json_report(
    result: ScanResult,
    *,
    top: int,
    dir_top: int,
    min_size: int,
) -> str:
    data = build_report_data(result, top=top, dir_top=dir_top, min_size=min_size)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
