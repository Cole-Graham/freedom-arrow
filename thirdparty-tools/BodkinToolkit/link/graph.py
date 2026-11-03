"""Entity-graph construction + link_info computation.

Reads every table from db (via `db dump`, snake_case rows), builds an
in-memory adjacency graph, and computes the derived `link_info` block for any
canonical entity. Pure computation: no writes, no storage knowledge.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List

import yaml
try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

from ..core import proc

CANONICAL = ("units", "weapons", "ammunition", "turrets", "modifications", "options")
BRIDGE = ("turret_units", "turret_weapons", "squad_members", "squad_weapons",
          "weapon_ammunitions")
ALL_TABLES = CANONICAL + BRIDGE

# bridge tables carry no link_info
BRIDGE_SET = set(BRIDGE)


def load_tables() -> Dict[str, List[Dict[str, Any]]]:
    """Pull every table out of db as typed rows."""
    data = {}
    for t in ALL_TABLES:
        r = proc.run_tool("db", "dump", t, capture=True)
        data[t] = yaml.load(r.stdout, Loader=_Loader) if r.stdout else []
        data[t] = data[t] or []
    return data


def _index(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {r["id"]: r for r in rows if "id" in r}


def _name(idx: Dict[int, Dict[str, Any]], i: int) -> str:
    row = idx.get(i)
    if not row:
        return f"<missing id {i}>"
    return row.get("name") or f"<id {i}>"


def _ui_name(idx: Dict[int, Dict[str, Any]], i: int) -> str:
    row = idx.get(i) or {}
    return row.get("ui_name") or f"<missing id {i}>"


def _ref_list(ids: Iterable[int], idx: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"id": i, "name": _name(idx, i)} for i in sorted(ids)]


def _ref_list_ui(ids: Iterable[int], idx: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"id": i, "ui_name": _ui_name(idx, i)} for i in sorted(ids)]


class Graph:
    def __init__(self, data: Dict[str, List[Dict[str, Any]]]):
        self.units_idx = _index(data["units"])
        self.weapons_idx = _index(data["weapons"])
        self.ammo_idx = _index(data["ammunition"])
        self.turrets_idx = _index(data["turrets"])
        self.mods_idx = _index(data["modifications"])
        self.options_idx = _index(data["options"])

        self.unit_turrets = defaultdict(set)
        self.turret_units = defaultdict(set)
        for r in data["turret_units"]:
            self.unit_turrets[r["unit_id"]].add(r["turret_id"])
            self.turret_units[r["turret_id"]].add(r["unit_id"])

        # turret hierarchy (self-reference via parent_turret_id)
        self.turret_parent = {}
        self.turret_children = defaultdict(set)
        for r in data["turrets"]:
            p = r.get("parent_turret_id")
            if p:
                self.turret_parent[r["id"]] = p
                self.turret_children[p].add(r["id"])

        self.turret_weapons = defaultdict(set)
        self.weapon_turrets = defaultdict(set)
        for r in data["turret_weapons"]:
            self.turret_weapons[r["turret_id"]].add(r["weapon_id"])
            self.weapon_turrets[r["weapon_id"]].add(r["turret_id"])

        self.weapon_units = defaultdict(set)
        self.weapon_ammo = defaultdict(set)
        self.ammo_weapons = defaultdict(set)
        self.ammo_units = defaultdict(set)
        self.unit_weapons = defaultdict(set)
        self.unit_ammo = defaultdict(set)
        for r in data["weapon_ammunitions"]:
            u, w, a = r["unit_id"], r["weapon_id"], r["ammunition_id"]
            self.weapon_units[w].add(u)
            self.weapon_ammo[w].add(a)
            self.ammo_weapons[a].add(w)
            self.ammo_units[a].add(u)
            self.unit_weapons[u].add(w)
            self.unit_ammo[u].add(a)

        self.unit_squad_weapons = defaultdict(set)
        for r in data["squad_weapons"]:
            self.unit_squad_weapons[r["unit_id"]].add(r["weapon_id"])
            self.weapon_units[r["weapon_id"]].add(r["unit_id"])
            self.unit_weapons[r["unit_id"]].add(r["weapon_id"])
        for r in data["squad_members"]:
            for k in ("primary_weapon_id", "special_weapon_id"):
                wid = r.get(k)
                if wid:
                    self.unit_squad_weapons[r["unit_id"]].add(wid)
                    self.weapon_units[wid].add(r["unit_id"])
                    self.unit_weapons[r["unit_id"]].add(wid)

        # weapons reachable through turrets a unit carries
        for uid, tids in self.unit_turrets.items():
            for tid in tids:
                for wid in self.turret_weapons.get(tid, ()):
                    self.unit_weapons[uid].add(wid)
                    self.weapon_units[wid].add(uid)

        self.unit_mods = defaultdict(list)
        for r in sorted(data["modifications"], key=lambda x: x["id"]):
            self.unit_mods[r["unit_id"]].append(r["id"])

        self.mod_options = defaultdict(list)
        for r in sorted(data["options"], key=lambda x: x["id"]):
            self.mod_options[r["modification_id"]].append(r["id"])

        # hardpoints: per unit, per slot -> set of turret ids any option places there
        self.unit_hardpoints = defaultdict(lambda: defaultdict(set))
        mod_unit = {m["id"]: m["unit_id"] for m in data["modifications"]}
        for o in data["options"]:
            uid = mod_unit.get(o.get("modification_id"))
            if not uid:
                continue
            for slot, tid in (o.get("turret_overrides") or {}).items():
                if tid:
                    self.unit_hardpoints[uid][int(slot)].add(tid)

    # -- per-entity link blocks ----------------------------------------------

    def _mods_with_options(self, mod_ids):
        out = []
        for mid in mod_ids:
            entry = {"id": mid, "ui_name": _ui_name(self.mods_idx, mid)}
            opt_ids = sorted(self.mod_options.get(mid, ()))
            if opt_ids:
                entry["options"] = [
                    {"id": oid, "ui_name": _ui_name(self.options_idx, oid)}
                    for oid in opt_ids
                ]
            out.append(entry)
        return out

    def _hardpoints(self, uid):
        out = []
        slot_map = self.unit_hardpoints.get(uid, {})
        for slot in sorted(slot_map):
            tids = sorted(slot_map[slot])
            if tids:
                out.append({"slot": slot,
                            "turrets": [{"id": t, "name": _name(self.turrets_idx, t)}
                                        for t in tids]})
        return out

    def links_for_unit(self, uid):
        return {
            "weapons": _ref_list(self.unit_weapons.get(uid, ()), self.weapons_idx),
            "ammunition": _ref_list(self.unit_ammo.get(uid, ()), self.ammo_idx),
            "turrets": _ref_list(self.unit_turrets.get(uid, ()), self.turrets_idx),
            "squad_weapons": _ref_list(self.unit_squad_weapons.get(uid, ()), self.weapons_idx),
            "modifications": self._mods_with_options(sorted(self.unit_mods.get(uid, ()))),
            "hardpoints": self._hardpoints(uid),
        }

    def links_for_weapon(self, wid):
        return {
            "ammunition": _ref_list(self.weapon_ammo.get(wid, ()), self.ammo_idx),
            "units": _ref_list(self.weapon_units.get(wid, ()), self.units_idx),
            "turrets": _ref_list(self.weapon_turrets.get(wid, ()), self.turrets_idx),
        }

    def links_for_ammo(self, aid):
        return {
            "weapons": _ref_list(self.ammo_weapons.get(aid, ()), self.weapons_idx),
            "units": _ref_list(self.ammo_units.get(aid, ()), self.units_idx),
        }

    def links_for_turret(self, tid):
        block = {
            "units": _ref_list(self.turret_units.get(tid, ()), self.units_idx),
            "weapons": _ref_list(self.turret_weapons.get(tid, ()), self.weapons_idx),
            "children": _ref_list(self.turret_children.get(tid, ()), self.turrets_idx),
        }
        p = self.turret_parent.get(tid)
        if p:
            block["parent"] = {"id": p, "name": _name(self.turrets_idx, p)}
        return block

    # -- turret-hierarchy validation ------------------------------------------

    def orphans_for_unit(self, uid):
        """Return turret-hierarchy violations for a unit's loadout options.

        A unit's cupola/sub-turrets are turret_units children of a main turret;
        an option's `turret_overrides` picks which turret occupies each slot.
        If an option places a turret that has NO sub-turrets into a slot whose
        other variants DO have sub-turrets, those sub-turrets lose their parent
        (orphaned) when that option is applied -> in-game UI breakage.

        Returns a list of dicts:
          {option_id, option_name, slot, placed_turret, orphaned: [turret ids]}
        Plus structural orphans (a unit turret whose parent the unit lacks).
        """
        warnings = []
        unit_turrets = set(self.unit_turrets.get(uid, ()))

        # structural: a turret on the unit whose parent the unit does not carry
        for tid in sorted(unit_turrets):
            p = self.turret_parent.get(tid)
            if p and p not in unit_turrets:
                warnings.append({"option_id": None, "option_name": "(base loadout)",
                                 "slot": None, "placed_turret": tid,
                                 "orphaned": [tid],
                                 "reason": f"turret #{tid} parent #{p} not on unit"})

        # option-displacement: per slot, collect the turret variants this unit
        # places there across all its options.
        opt_ids = [oid for mid in self.unit_mods.get(uid, ()) for oid in self.mod_options.get(mid, ())]
        slot_variants = defaultdict(set)
        for oid in opt_ids:
            for slot, t in (self.options_idx.get(oid, {}).get("turret_overrides") or {}).items():
                slot_variants[int(slot)].add(t)

        for oid in opt_ids:
            o = self.options_idx.get(oid, {})
            for slot, t in (o.get("turret_overrides") or {}).items():
                slot = int(slot)
                if self.turret_children.get(t):
                    continue  # placed turret brings its own children -> fine
                # alternatives at this slot that DO carry children
                orphaned = set()
                for alt in slot_variants[slot]:
                    if alt != t:
                        orphaned |= self.turret_children.get(alt, set())
                if orphaned:
                    warnings.append({
                        "option_id": oid,
                        "option_name": o.get("ui_name") or f"#{oid}",
                        "slot": slot, "placed_turret": t,
                        "orphaned": sorted(orphaned),
                        "reason": (f"turret #{t} has no sub-turrets but other slot-{slot} "
                                   f"variants do; their cupolas are orphaned")})
        return warnings

    def links_for_modification(self, mid):
        row = self.mods_idx.get(mid, {})
        out = {}
        uid = row.get("unit_id")
        if uid:
            out["unit"] = {"id": uid, "name": _name(self.units_idx, uid)}
        out["options"] = _ref_list_ui(self.mod_options.get(mid, ()), self.options_idx)
        return out

    def links_for_option(self, oid):
        row = self.options_idx.get(oid, {})
        out = {}
        mid = row.get("modification_id")
        if mid:
            out["modification"] = {"id": mid, "ui_name": _ui_name(self.mods_idx, mid)}
            muid = (self.mods_idx.get(mid) or {}).get("unit_id")
            if muid:
                out["unit"] = {"id": muid, "name": _name(self.units_idx, muid)}
        return out

    _DISPATCH = {
        "units": "links_for_unit",
        "weapons": "links_for_weapon",
        "ammunition": "links_for_ammo",
        "turrets": "links_for_turret",
        "modifications": "links_for_modification",
        "options": "links_for_option",
    }

    def compute(self, table: str, entity_id: int) -> Dict[str, Any]:
        """Return the link_info block for one entity (empty keys dropped)."""
        fn = getattr(self, self._DISPATCH[table])
        block = fn(entity_id)
        return {k: v for k, v in block.items() if v}

    def exists(self, table: str, entity_id: int) -> bool:
        idx = {
            "units": self.units_idx, "weapons": self.weapons_idx,
            "ammunition": self.ammo_idx, "turrets": self.turrets_idx,
            "modifications": self.mods_idx, "options": self.options_idx,
        }[table]
        return entity_id in idx
