"""Structural bridge-table mutations for `bond replace`, ported from v2
mutations.py but operating on the db-backed Tables cache.

Each function mutates the cache in memory and returns log lines; the caller
flushes once at the end.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .tables import Tables


def _name_of(t: Tables, table: str, _id: int) -> str:
    for r in t.get(table):
        if r.get("id") == _id:
            return r.get("name", f"<id {_id}>")
    return f"<missing id {_id}>"


def turret_units_for(t: Tables, turret_id: int) -> List[int]:
    return sorted({r["unit_id"] for r in t.get("turret_units")
                   if r["turret_id"] == turret_id})


def turrets_carrying_weapon_for_unit(t: Tables, unit_id: int,
                                     weapon_id: int) -> List[Tuple[int, List[int]]]:
    tu = t.get("turret_units")
    tw = t.get("turret_weapons")
    unit_turrets = {r["turret_id"] for r in tu if r["unit_id"] == unit_id}
    weapon_turrets = {r["turret_id"] for r in tw if r["weapon_id"] == weapon_id}
    out = []
    for tid in sorted(unit_turrets & weapon_turrets):
        sharers = sorted({r["unit_id"] for r in tu if r["turret_id"] == tid})
        out.append((tid, sharers))
    return out


def _child_turret_ids(t: Tables, parent_id: int) -> List[int]:
    return [r["id"] for r in t.get("turrets") if r.get("parent_turret_id") == parent_id]


def clone_turret_for_unit(t: Tables, turret_id: int, unit_id: int) -> Tuple[int, List[str]]:
    turrets = t.get("turrets")
    tu_rows = t.get("turret_units")
    tw_rows = t.get("turret_weapons")
    log: List[str] = []
    unit_name = _name_of(t, "units", unit_id)

    to_clone = [turret_id]
    stack = [turret_id]
    while stack:
        cur = stack.pop()
        kids = _child_turret_ids(t, cur)
        to_clone.extend(kids)
        stack.extend(kids)

    old_to_new: Dict[int, int] = {}
    for old in to_clone:
        nid = t.next_id("turrets")
        old_to_new[old] = nid
        src = next(r for r in turrets if r["id"] == old)
        new_row = dict(src)
        new_row["id"] = nid
        base = src.get("name", f"turret#{old}")
        new_row["name"] = f"{base} (clone for {unit_name})"
        new_row["cloned_from"] = src.get("cloned_from", old)
        pp = new_row.get("parent_turret_id")
        if pp in old_to_new:
            new_row["parent_turret_id"] = old_to_new[pp]
        turrets.append(new_row)
        t.mark("turrets")
        log.append(f"cloned turret #{old} -> #{nid} ({new_row['name']})")

    for r in list(tw_rows):
        if r["turret_id"] in old_to_new:
            clone = dict(r)
            clone["id"] = t.next_id("turret_weapons")
            clone["turret_id"] = old_to_new[r["turret_id"]]
            tw_rows.append(clone)
            t.mark("turret_weapons")
            log.append(f"  + turret_weapons #{clone['id']} "
                       f"(turret #{clone['turret_id']} weapon #{clone['weapon_id']})")

    repointed = 0
    for r in tu_rows:
        if r["unit_id"] == unit_id and r["turret_id"] == turret_id:
            r["turret_id"] = old_to_new[turret_id]
            repointed += 1
    if repointed:
        t.mark("turret_units")
    log.append(f"repointed {repointed} turret_units row(s) for unit #{unit_id} "
               f"-> turret #{old_to_new[turret_id]}")
    return old_to_new[turret_id], log


def swap_weapon_in_turret(t: Tables, turret_id: int, old_w: int, new_w: int) -> List[str]:
    rows = t.get("turret_weapons")
    changed = 0
    for r in rows:
        if r["turret_id"] == turret_id and r["weapon_id"] == old_w:
            r["weapon_id"] = new_w
            changed += 1
    if changed:
        t.mark("turret_weapons")
    return [f"swapped {changed} turret_weapons row(s) on turret #{turret_id}: "
            f"weapon #{old_w} -> #{new_w}"]


def swap_squad_weapon(t: Tables, unit_id: int, old_w: int, new_w: int) -> List[str]:
    log = []
    sw = t.get("squad_weapons")
    changed = 0
    for r in sw:
        if r["unit_id"] == unit_id and r["weapon_id"] == old_w:
            r["weapon_id"] = new_w
            changed += 1
    if changed:
        t.mark("squad_weapons")
        log.append(f"swapped {changed} squad_weapons row(s) on unit #{unit_id}: "
                   f"#{old_w} -> #{new_w}")
    sm = t.get("squad_members")
    primary = special = 0
    for r in sm:
        if r["unit_id"] != unit_id:
            continue
        if r.get("primary_weapon_id") == old_w:
            r["primary_weapon_id"] = new_w
            primary += 1
        if r.get("special_weapon_id") == old_w:
            r["special_weapon_id"] = new_w
            special += 1
    if primary or special:
        t.mark("squad_members")
    if primary:
        log.append(f"swapped {primary} squad_members.primary_weapon_id on unit #{unit_id}")
    if special:
        log.append(f"swapped {special} squad_members.special_weapon_id on unit #{unit_id}")
    return log


def drop_unit_weapon_ammo(t: Tables, unit_id: int, weapon_id: int) -> List[str]:
    rows = t.get("weapon_ammunitions")
    before = len(rows)
    kept = [r for r in rows if not (r["unit_id"] == unit_id and r["weapon_id"] == weapon_id)]
    t._cache["weapon_ammunitions"] = kept
    if len(kept) != before:
        t.mark("weapon_ammunitions")
    return [f"dropped {before - len(kept)} weapon_ammunitions row(s) "
            f"for (unit #{unit_id}, weapon #{weapon_id})"]


def attach_unit_weapon_ammo(t: Tables, unit_id: int, weapon_id: int,
                            ammo_ids, default_qty: int = 1) -> List[str]:
    rows = t.get("weapon_ammunitions")
    log = []
    for aid in ammo_ids:
        if any(r["unit_id"] == unit_id and r["weapon_id"] == weapon_id
               and r["ammunition_id"] == aid for r in rows):
            continue
        nid = t.next_id("weapon_ammunitions")
        rows.append({"id": nid, "unit_id": unit_id, "weapon_id": weapon_id,
                     "ammunition_id": aid, "order": 0, "quantity": default_qty})
        t.mark("weapon_ammunitions")
        log.append(f"attached ammo #{aid} -> unit #{unit_id} weapon #{weapon_id} "
                   f"(row id {nid})")
    return log
