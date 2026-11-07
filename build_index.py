#!/usr/bin/env python3
"""Rebuild index.json from the map files in maps/.

Runs in this repo's GitHub Action on every upload. Every TDS Helper reads
index.json on start, downloads the maps it lists, and checks each file's
SHA-256 against the value recorded here.

A file that fails the checks below is left OUT of the index and the run is
marked failed, so the uploader sees a red X with the reason - and nobody's
app ever downloads a broken map.

    python build_index.py          # write index.json
    python build_index.py --check  # exit 1 if any file is rejected
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAPS = ROOT / "maps"
NAME_RE = re.compile(r"^[a-z0-9_]{1,60}\.tdsmap\.json$")
MAX_BYTES = 512 * 1024
MIN_SEPARATION = 0.055
STANDARD_SPOTS = (
    "early_dps_1", "early_dps_2", "early_dps_3",
    "mid_dps_1", "mid_dps_2", "mid_dps_3",
    "late_dps_1", "late_dps_2",
    "aoe_1", "aoe_2",
    "support_1", "support_2", "support_3",
    "farm_1", "farm_2", "farm_3", "farm_4",
    "boss_dps_1", "boss_dps_2",
    "flex_1", "flex_2",
)


def check(path: Path) -> tuple[dict | None, str]:
    if not NAME_RE.match(path.name):
        return None, "file name must look like my_map.tdsmap.json (lowercase, digits, _)"
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        return None, "file is too large"
    try:
        raw = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"not valid JSON: {exc}"
    if not isinstance(raw, dict) or raw.get("format") != "tds-helper-map":
        return None, "not a TDS Helper map export"
    spots = raw.get("spots")
    if not isinstance(spots, dict):
        return None, "no spots"
    missing = [key for key in STANDARD_SPOTS if key not in spots]
    if missing:
        return None, f"missing spots: {', '.join(missing)}"
    points = []
    for key, spec in spots.items():
        if not isinstance(spec, dict):
            return None, f"spot {key} is malformed"
        x, y = spec.get("x"), spec.get("y")
        for value in (x, y):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                return None, f"spot {key} has a coordinate outside 0..1"
        points.append((key, float(x), float(y)))
    for i, (a, ax, ay) in enumerate(points):
        for b, bx, by in points[i + 1:]:
            if math.hypot(ax - bx, ay - by) < MIN_SEPARATION:
                return None, f"spots {a} and {b} overlap"
    entry = {
        "id": path.name[: -len(".tdsmap.json")],
        "name": str(raw.get("name") or path.stem)[:60],
        "file": f"maps/{path.name}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "confidence": str(raw.get("confidence", "scanned"))[:20],
    }
    return entry, ""


def build() -> tuple[list[dict], list[tuple[str, str]]]:
    entries, rejected = [], []
    for path in sorted(MAPS.glob("*")):
        if path.name.startswith(".") or path.is_dir():
            continue
        entry, reason = check(path)
        if entry is None:
            rejected.append((path.name, reason))
        else:
            entries.append(entry)
    return entries, rejected


def main() -> int:
    entries, rejected = build()
    for name, reason in rejected:
        print(f"REJECTED {name}: {reason}")
    if "--check" in sys.argv:
        return 1 if rejected else 0
    index = {"format": "tds-helper-library", "version": 1, "maps": entries}
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"index.json: {len(entries)} map(s), {len(rejected)} rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
