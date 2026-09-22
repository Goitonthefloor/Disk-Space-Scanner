"""Tests for size parsing and formatting."""

import pytest

from dss.sizes import format_size, parse_size


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", 0),
        ("512", 512),
        ("1KB", 1000),
        ("1KiB", 1024),
        ("100MB", 100_000_000),
        ("1.5GiB", int(1.5 * 1024**3)),
        ("2gb", 2_000_000_000),
        ("1T", 1000**4),
    ],
)
def test_parse_size(text: str, expected: int) -> None:
    assert parse_size(text) == expected


def test_parse_size_invalid() -> None:
    with pytest.raises(ValueError):
        parse_size("big")


def test_format_size() -> None:
    assert format_size(0) == "0 B"
    assert format_size(1023) == "1023 B"
    assert format_size(1024) == "1.0 KiB"
    assert format_size(100 * 1024**2) == "100.0 MiB"
