"""Markdown research-table parser (ported from v2 research_to_yaml).

Each file is a Markdown table with at least 'Entry ID' and 'Effective Range'
columns, optionally 'Altitude'. Ranges use the '<number>m' convention with
optional thousands separators.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

ID_TOKEN = re.compile(r"(\d+)\s*-\s*(\d+)|(\d+)")
METER_VALUE = re.compile(r"(\d[\d,]*)\s*m\b", re.IGNORECASE)


def parse_id_cell(cell: str) -> List[int]:
    cell = re.sub(r"\([^)]*\)", "", cell)
    ids: List[int] = []
    for m in ID_TOKEN.finditer(cell):
        lo, hi, single = m.groups()
        if single is not None:
            ids.append(int(single))
        elif lo and hi:
            a, b = int(lo), int(hi)
            if b - a <= 200:
                ids.extend(range(a, b + 1))
            else:
                ids.extend([a, b])
    return ids


def parse_meters(cell: str) -> Optional[int]:
    m = METER_VALUE.search(cell)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def parse_research_md(path: Path) -> Dict[int, Dict[str, Optional[int]]]:
    """Return {ammo_id: {'range': meters, 'alt': meters or None}}."""
    out: Dict[int, Dict[str, Optional[int]]] = {}
    in_table = False
    headers: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not in_table:
                headers = [c.lower() for c in cells]
                if any("entry id" in h for h in headers):
                    in_table = True
                continue
            if len(cells) < 2:
                continue
            id_col = next((i for i, h in enumerate(headers) if "entry id" in h), 0)
            range_col = next(
                (i for i, h in enumerate(headers)
                 if "effective range" in h or h == "range"), None)
            if range_col is None:
                range_col = next((i for i, h in enumerate(headers) if "range" in h), None)
            if range_col is None:
                continue
            alt_col = next((i for i, h in enumerate(headers) if "altitude" in h), None)
            ids = parse_id_cell(cells[id_col])
            if not ids:
                continue
            rng = parse_meters(cells[range_col]) if range_col < len(cells) else None
            alt = parse_meters(cells[alt_col]) if alt_col is not None and alt_col < len(cells) else None
            if rng is None and alt is None:
                continue
            for aid in ids:
                out[aid] = {"range": rng, "alt": alt}
        elif line.startswith("#") or line.strip() == "":
            in_table = False
            headers = []
    return out
