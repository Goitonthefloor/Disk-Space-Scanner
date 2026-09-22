"""Human-readable size parsing and formatting."""

from __future__ import annotations

import re

_SIZE_RE = re.compile(
    r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[kmgtpe]?i?b?)?\s*$",
    re.IGNORECASE,
)

_UNIT_FACTORS: dict[str, int] = {
    "": 1,
    "b": 1,
    "k": 1000,
    "kb": 1000,
    "kib": 1024,
    "m": 1000**2,
    "mb": 1000**2,
    "mib": 1024**2,
    "g": 1000**3,
    "gb": 1000**3,
    "gib": 1024**3,
    "t": 1000**4,
    "tb": 1000**4,
    "tib": 1024**4,
    "p": 1000**5,
    "pb": 1000**5,
    "pib": 1024**5,
    "e": 1000**6,
    "eb": 1000**6,
    "eib": 1024**6,
}

_BINARY_UNITS = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")


def parse_size(text: str) -> int:
    """Parse a size string like ``100MB``, ``1.5GiB`` or ``512`` into bytes."""
    match = _SIZE_RE.match(text)
    if not match:
        raise ValueError(f"Invalid size: {text!r}")

    value = float(match.group("value"))
    unit = (match.group("unit") or "").lower()
    if unit not in _UNIT_FACTORS:
        raise ValueError(f"Unknown size unit in {text!r}")

    return int(value * _UNIT_FACTORS[unit])


def format_size(num_bytes: int | float) -> str:
    """Format a byte count as a human-readable binary size string."""
    value = float(max(0, num_bytes))
    for unit in _BINARY_UNITS:
        if value < 1024.0 or unit == _BINARY_UNITS[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} {_BINARY_UNITS[-1]}"
