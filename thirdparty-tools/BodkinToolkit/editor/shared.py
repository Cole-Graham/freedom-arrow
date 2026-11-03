"""Shared-reference detection + clone-or-alter prompt.

Many child entities (armors, mobility, sensors, abilities, turrets) are shared
by several units. Editing one in place changes every user. Before editing,
ask the user whether to clone a private copy for this unit or alter in place.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core import out, prompt
from .dbio import Tables, pk_of


def unit_name(t: Tables, uid: int) -> str:
    u = t.by_id("units", uid)
    return u.get("name") if u else f"#{uid}"


def other_users(t: Tables, bridge: str, ref_field: str, ref_id: int,
                this_unit: int, unit_field: str = "UnitId") -> List[int]:
    """Unit ids (other than this_unit) whose bridge rows point at ref_id."""
    return sorted({r[unit_field] for r in t.get(bridge)
                   if r.get(ref_field) == ref_id and r.get(unit_field) != this_unit})


def clone_or_alter(t: Tables, ref_table: str, ref_id: int, bridge: str,
                   ref_field: str, this_unit: int, yes: bool = False,
                   unit_field: str = "UnitId") -> int:
    """Return the ref id the caller should edit.

    If ref_id is shared with other units, prompt: clone a private copy (repoint
    this unit's bridge rows to it) or alter in place. Returns the (possibly new)
    ref id. With yes=True, auto-clones when shared.
    """
    sharers = other_users(t, bridge, ref_field, ref_id, this_unit, unit_field)
    if not sharers:
        return ref_id

    names = ", ".join(unit_name(t, u) for u in sharers)
    out.emit(f"  This {ref_table} entry (#{ref_id}) is also used by: {names}")
    clone = yes or prompt.confirm(
        f"Clone a private copy for this unit? (No = alter in place, affects all)",
        default=True)
    if not clone:
        return ref_id

    pk = pk_of(ref_table)
    src = t.by_id(ref_table, ref_id)
    new_id = t.next_id(ref_table)
    new_row = dict(src)
    new_row[pk] = new_id
    if "Name" in new_row and isinstance(new_row["Name"], str):
        new_row["Name"] = f"{new_row['Name']} (clone for {unit_name(t, this_unit)})"
    t.add(ref_table, new_row)

    repointed = 0
    for r in t.get(bridge):
        if r.get(ref_field) == ref_id and r.get(unit_field) == this_unit:
            r[ref_field] = new_id
            repointed += 1
    if repointed:
        t.mark(bridge)
    out.emit(f"  cloned {ref_table} #{ref_id} -> #{new_id}; repointed {repointed} link(s)")
    return new_id
