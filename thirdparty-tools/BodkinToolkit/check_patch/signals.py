"""Diagnostic signals over db ammunition/options.

- scale signal: ammo rows whose current differs from vanilla.
- option fingerprints: author sentinels in ui_name.
- is_default sanity: each modification should have exactly one default option.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

FINGERPRINTS = {"test", "custom_option_empty", "__zombie__"}


def scale_signal(ammo_rows: List[Dict[str, Any]]) -> int:
    n = 0
    for r in ammo_rows:
        cur, van = r.get("current") or {}, r.get("vanilla") or {}
        if any(cur.get(k) != van.get(k) for k in ("ground", "low_alt", "high_alt")):
            n += 1
    return n


def fingerprint_count(option_rows: List[Dict[str, Any]]) -> int:
    return sum(1 for r in option_rows
               if (r.get("ui_name") or "").strip().lower() in FINGERPRINTS)


def default_anomalies(option_rows: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
    """Return (modification_id, default_count) for mods whose default count is
    not exactly 1."""
    counts = defaultdict(int)
    seen = set()
    for r in option_rows:
        mid = r.get("modification_id")
        seen.add(mid)
        if r.get("is_default"):
            counts[mid] += 1
    return [(mid, counts.get(mid, 0)) for mid in sorted(seen, key=lambda x: (x is None, x))
            if counts.get(mid, 0) != 1]
