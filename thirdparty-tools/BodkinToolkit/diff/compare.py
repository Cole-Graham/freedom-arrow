"""Row / id-set / field diff logic for game JSON. Read-only; no db.

Ported from v2 diff_json. Loads JSON (optionally tolerant of a truncated
tail), diffs id sets per file, and optionally renders per-id field diffs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core import out


def load_json(path: Path, tolerant: bool) -> Optional[List[Dict[str, Any]]]:
    try:
        txt = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        if not tolerant:
            return e  # type: ignore[return-value]
        last = txt.rfind("  },")
        if last < 0:
            return None
        repaired = txt[:last + 4].rstrip().rstrip(",") + "\n]\n"
        try:
            rows = json.loads(repaired)
            out.emit(f"  WARN {path.name} repaired tail, {len(rows)} rows recovered")
            return rows
        except json.JSONDecodeError:
            return None


def summarize_row(row: Dict[str, Any]) -> str:
    for k in ("Name", "HUDName", "UIName", "OriginalName"):
        v = row.get(k)
        if v:
            return f"{k}={v!r}"
    return "(no name)"


def id_diff(left_rows, right_rows) -> Tuple[set, set]:
    li = {r["Id"] for r in left_rows if "Id" in r}
    ri = {r["Id"] for r in right_rows if "Id" in r}
    return li - ri, ri - li


def field_diff(left_rows, right_rows) -> List[Tuple[Any, List[Tuple[str, Any, Any]]]]:
    """Per id present in both sides, list (field, left_value, right_value) for
    every field whose value changed."""
    li = {r["Id"]: r for r in left_rows if "Id" in r}
    ri = {r["Id"]: r for r in right_rows if "Id" in r}
    changed = []
    _missing = object()
    for i in sorted(set(li) & set(ri)):
        a, b = li[i], ri[i]
        keys = set(a) | set(b)
        d = [(k, a.get(k), b.get(k)) for k in sorted(keys) if a.get(k) != b.get(k)]
        if d:
            changed.append((i, d))
    return changed


def fmt_val(v: Any) -> str:
    """Compact one-line display of a field value."""
    s = repr(v)
    return s if len(s) <= 60 else s[:57] + "..."
