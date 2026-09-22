"""Command-line interface for Disk-Space-Scanner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .report import format_json_report, format_text_report
from .scanner import scan
from .sizes import parse_size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dss",
        description=(
            "Disk-Space-Scanner: analyse local directory trees to find "
            "storage hotspots and large files. Analysis only — no deletes."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser(
        "scan",
        help="Scan a directory for large files and directory hotspots",
    )
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan (default: current working directory)",
    )
    scan_parser.add_argument(
        "--min-size",
        default="0",
        metavar="SIZE",
        help="Only list files at least this large (e.g. 100MB, 1GiB). Default: 0",
    )
    scan_parser.add_argument(
        "--top",
        type=int,
        default=20,
        metavar="N",
        help="Show the N largest matching files (default: 20)",
    )
    scan_parser.add_argument(
        "--dir-top",
        type=int,
        default=15,
        metavar="N",
        help="Show the N largest directories (default: 15)",
    )
    scan_parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links while scanning (off by default)",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON (useful for CI / scripts)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return _cmd_scan(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _cmd_scan(args: argparse.Namespace) -> int:
    if args.top < 0 or args.dir_top < 0:
        print("error: --top and --dir-top must be >= 0", file=sys.stderr)
        return 2

    try:
        min_size = parse_size(args.min_size)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    root = Path(args.path)
    try:
        result = scan(
            root,
            min_size=min_size,
            follow_symlinks=args.follow_symlinks,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        sys.stdout.write(
            format_json_report(
                result,
                top=args.top,
                dir_top=args.dir_top,
                min_size=min_size,
            )
        )
    else:
        sys.stdout.write(
            format_text_report(
                result,
                top=args.top,
                dir_top=args.dir_top,
                min_size=min_size,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
