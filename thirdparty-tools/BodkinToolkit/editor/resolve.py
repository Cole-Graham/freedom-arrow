"""Resolve entities by exact id or partial (case-insensitive) name, with an
interactive disambiguation menu when a partial matches several."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core import ui
from .dbio import Tables, pk_of


def unit_label(u: Dict[str, Any]) -> str:
    hud = u.get("hud_name")
    extra = f" [{hud}]" if hud and hud != u.get("name") else ""
    return f"#{u.get('id')}  {u.get('name')}{extra}"


def _name_fields(table: str) -> List[str]:
    # passthrough tables use PascalCase; core tables snake
    if table in ("units", "weapons", "ammunition", "turrets"):
        return ["name", "hud_name"]
    if table in ("modifications", "options"):
        return ["ui_name"]
    return ["Name", "UIName", "HUDName"]


def resolve(t: Tables, table: str, query: str,
            label_fn=None, prompt_msg: str = "Multiple matches - pick one:") -> Optional[Dict[str, Any]]:
    """query is an exact id (all digits) or a partial name (ci substring)."""
    pk = pk_of(table)
    rows = t.get(table)
    q = (query or "").strip()
    if q == "":
        return None
    if q.lstrip("-").isdigit():
        return t.by_id(table, int(q))
    ql = q.lower()
    fields = _name_fields(table)
    # exact (case-insensitive) name match wins outright
    exact = [r for r in rows if any(str(r.get(f, "")).lower() == ql for f in fields)]
    if len(exact) == 1:
        return exact[0]
    hits = exact or [r for r in rows
                     if any(str(r.get(f, "")).lower().find(ql) >= 0 for f in fields)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    lf = label_fn or (lambda r: f"#{r.get(pk)}  " +
                      " / ".join(str(r.get(f)) for f in fields if r.get(f)))
    return ui.choose_one(prompt_msg, hits, label_fn=lf)


def resolve_unit(t: Tables, query: str) -> Optional[Dict[str, Any]]:
    return resolve(t, "units", query, label_fn=unit_label,
                   prompt_msg="Multiple units match - pick one:")
