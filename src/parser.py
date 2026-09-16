#!/usr/bin/env python3
"""Parse raw TCS GPS capture lines into the target JSON structure.

A raw line looks like:

    2026-09-14 00:33:04,79021,<<LIP-SHORT,"-45.73773623,-68.28815103,1.1,1.0"

Splitting on commas yields 7 fields:
    0: date        -> "2026-09-14 00:33:04"
    1: tetra       -> "79021"
    2: message     -> "<<LIP-SHORT"
    3: latitude    -> "-45.73773623"   (leading quote stripped)
    4: longitude   -> "-68.28815103"
    5: field6      -> "1.1"
    6: field7      -> "1.0"            (trailing quote stripped)
"""
from __future__ import annotations

import json
from typing import Any, Dict


class ParseError(ValueError):
    """Raised when a raw line cannot be parsed into the expected structure."""


def _to_int(value: str) -> int:
    """Convert a numeric string to int, tolerating float-like values ("1.0")."""
    return int(float(value))


def parse_line(line: str) -> Dict[str, Any]:
    """Parse a single raw capture line into the target dict structure.

    Raises ParseError if the line does not have the expected shape.
    """
    raw = line.strip()
    if not raw:
        raise ParseError("empty line")

    # The GPS payload is wrapped in double quotes; strip them so the numeric
    # fields split cleanly on commas.
    cleaned = raw.replace('"', "")
    parts = cleaned.split(",")

    if len(parts) != 7:
        raise ParseError(
            f"expected 7 comma-separated fields, got {len(parts)}: {raw!r}"
        )

    date, tetra, message, lat, lon, field6, field7 = parts

    try:
        payload: Dict[str, Any] = {
            "date": date.strip(),
            "tetra": tetra.strip(),
            "message": message.strip(),
            "coordenadas": {
                "lat": float(lat),
                "long": float(lon),
            },
            "field6": float(field6),
            "field7": float(field7),
        }
    except ValueError as exc:
        raise ParseError(f"could not parse numeric field in {raw!r}: {exc}") from exc

    return payload


def parse_to_json(line: str) -> str:
    """Parse a raw line and return a compact JSON string."""
    return json.dumps(parse_line(line), separators=(",", ":"))


if __name__ == "__main__":
    import sys

    sample = (
        '2026-09-14 00:33:04,79021,<<LIP-SHORT,'
        '"-45.73773623,-68.28815103,1.1,1.0"'
    )
    line = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sample
    print(json.dumps(parse_line(line), indent=2, ensure_ascii=False))
