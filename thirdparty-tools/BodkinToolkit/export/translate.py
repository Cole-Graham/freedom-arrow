"""Per-table inverse translation: db rows (snake_case, sparse) -> game JSON
(PascalCase, dense). Inverse of import/translate.py.

Canonical entities start from an existing JSON baseline so unmodelled game
fields survive the round trip; db-managed fields are overlaid on top. Bridge
tables are rebuilt wholesale. `link_info` is never written (game JSON has no
such concept).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# logical table -> game JSON filename
TABLE_FILE: Dict[str, str] = {
    "units": "Units.json",
    "weapons": "WeaponsJson.json",
    "ammunition": "AmmunitionsJson.json",
    "turrets": "TurretsJson.json",
    "turret_units": "TurretUnitsJson.json",
    "turret_weapons": "TurretWeaponsJson.json",
    "squad_members": "SquadMembersJson.json",
    "squad_weapons": "SquadWeaponsJson.json",
    "weapon_ammunitions": "WeaponAmmunitionsJson.json",
    "modifications": "ModificationsJson.json",
    "options": "OptionsJson.json",
    "countries": "CountriesJson.json",
    "specializations": "SpecializationsJson.json",
    "specialization_availabilities": "SpecializationAvailabilitiesJson.json",
    "transport_availabilities": "TransportAvailabilitiesJson.json",
    "armors": "ArmorsJson.json",
    "unit_armors": "UnitArmorsJson.json",
    "mobility": "MobilityJson.json",
    "unit_propulsions": "UnitPropulsionsJson.json",
    "fly_presets": "FlyPresetsJson.json",
    "sensors": "SensorsJson.json",
    "sensor_units": "SensorUnitsJson.json",
    "abilities": "AbilitiesJson.json",
    "unit_abilities": "UnitAbilitiesJson.json",
}

PASSTHROUGH = {
    "countries", "specializations", "specialization_availabilities",
    "transport_availabilities", "armors", "unit_armors", "mobility",
    "unit_propulsions", "fly_presets", "sensors", "sensor_units",
    "abilities", "unit_abilities",
}

# db field -> JSON key for simple scalar overlays on canonical entities
OVERLAY: Dict[str, Dict[str, str]] = {
    "units": {"name": "Name", "hud_name": "HUDName", "cost": "Cost",
              "stealth": "Stealth", "type": "Type", "role": "Role",
              "category": "CategoryType"},
    "weapons": {"name": "Name", "hud_name": "HUDName", "type": "Type"},
    "ammunition": {"name": "Name", "hud_name": "HUDName",
                   "target_type": "TargetType", "armor_targeted": "ArmorTargeted",
                   "trajectory": "TrajectoryType"},
    "turrets": {"name": "Name"},
}


def to_json_range(v: Any) -> float:
    """db real range -> JSON half-range. None->0; sentinels (<=0) preserved."""
    if v is None:
        return 0.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    if f <= 0.0:
        return f
    return f / 2.0


def _template(baseline: List[Dict[str, Any]]) -> Dict[str, Any]:
    return dict(baseline[0]) if baseline else {}


def _apply_overlay(kind: str, e: Dict[str, Any], jrow: Dict[str, Any]) -> None:
    for ykey, jkey in OVERLAY[kind].items():
        if ykey in e and e[ykey] is not None:
            jrow[jkey] = e[ykey]


# ── canonical builders ───────────────────────────────────────────────────────

def build_units(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    tmpl = _template(baseline)
    out = []
    for e in db_rows:
        jrow = dict(by_id.get(e["id"], tmpl))
        jrow["Id"] = e["id"]
        _apply_overlay("units", e, jrow)
        out.append(jrow)
    return out


def build_weapons(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    tmpl = _template(baseline)
    out = []
    for e in db_rows:
        jrow = dict(by_id.get(e["id"], tmpl))
        jrow["Id"] = e["id"]
        _apply_overlay("weapons", e, jrow)
        out.append(jrow)
    return out


def build_ammunition(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    tmpl = _template(baseline)
    out = []
    for e in db_rows:
        jrow = dict(by_id.get(e["id"], tmpl))
        jrow["Id"] = e["id"]
        _apply_overlay("ammunition", e, jrow)
        cur = e.get("current") or {}
        for ykey, jkey in (("ground", "GroundRange"), ("low_alt", "LowAltRange"),
                           ("high_alt", "HighAltRange")):
            if ykey in cur:
                jrow[jkey] = to_json_range(cur[ykey])
        mr = e.get("min_range") or {}
        if isinstance(mr, dict) and mr.get("ground") is not None:
            jrow["MinimalRange"] = float(mr["ground"])
        out.append(jrow)
    return out


def build_turrets(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    tmpl = _template(baseline)
    out = []
    for e in db_rows:
        tid = e["id"]
        if tid in by_id:
            jrow = dict(by_id[tid])
        else:
            src = by_id.get(e.get("cloned_from"))
            jrow = dict(src) if src is not None else dict(tmpl)
        jrow["Id"] = tid
        _apply_overlay("turrets", e, jrow)
        if "parent_turret_id" in e:
            jrow["ParentTurretId"] = e.get("parent_turret_id")
        if "is_default" in e:
            jrow["IsDefault"] = bool(e["is_default"])
        out.append(jrow)
    return out


def build_modifications(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    out = []
    for e in db_rows:
        t = by_id.get(e["id"], {})
        out.append({
            "Id": e["id"],
            "UnitId": e.get("unit_id", t.get("UnitId")),
            "Name": t.get("Name"),
            "Type": e.get("type", t.get("Type", 0)),
            "UIName": e.get("ui_name", t.get("UIName")),
            "ThumbnailFileName": e.get("thumbnail", t.get("ThumbnailFileName")),
            "Order": e.get("order", t.get("Order", 0)),
        })
    return out


def build_options(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    tmpl = _template(baseline)
    out = []
    for e in db_rows:
        jrow = dict(by_id.get(e["id"], tmpl))
        jrow["Id"] = e["id"]
        jrow["ModificationId"] = e.get("modification_id", jrow.get("ModificationId"))
        if "ui_name" in e:
            jrow["UIName"] = e["ui_name"]
        if "order" in e:
            jrow["Order"] = e["order"]
        if "is_default" in e:
            jrow["IsDefault"] = bool(e["is_default"])
        if "cost" in e:
            jrow["Cost"] = e["cost"]
        if "option_picture" in e:
            jrow["OptionPicture"] = e["option_picture"]
        for i in range(21):
            jrow[f"Turret{i}Id"] = 0
        for idx, v in (e.get("turret_overrides") or {}).items():
            jrow[f"Turret{int(idx)}Id"] = v
        for i in (1, 2, 3):
            jrow[f"Ability{i}Id"] = 0
        for idx, v in (e.get("ability_overrides") or {}).items():
            jrow[f"Ability{int(idx)}Id"] = v
        for ykey, jkey, default in (
            ("armor_id", "ArmorId", 0),
            ("mobility_id", "MobilityId", 0),
            ("main_sensor_id", "MainSensorId", 0),
            ("extra_sensor_id", "ExtraSensorId", 0),
            ("replace_unit_id", "ReplaceUnitId", 0),
            ("stealth_override", "StealthOverride", 0.0),
            ("time_modifier_refund", "TimeModifierRefund", 0.0),
            ("time_modifier_resurrect", "TimeModifierResurrect", 0.0),
        ):
            jrow[jkey] = e.get(ykey, default)
        for ykey, jkey in (
            ("concatenate_with_unit_name", "ConcatenateWithUnitName"),
            ("replace_unit_name", "ReplaceUnitName"),
            ("thumbnail_override", "ThumbnailOverride"),
            ("portrait_override", "PortraitOverride"),
            ("audio_preset_override", "AudioPresetOverride"),
        ):
            jrow[jkey] = e.get(ykey, None)
        out.append(jrow)
    return out


# ── bridge builders ──────────────────────────────────────────────────────────

def _assign_ids(rows, yaml_ids):
    used = {i for i in yaml_ids if i is not None}
    nxt = (max(used) + 1) if used else 1
    for r, yid in zip(rows, yaml_ids):
        if yid is None:
            r["Id"] = nxt
            used.add(nxt)
            nxt += 1
        else:
            r["Id"] = yid
    return rows


def build_turret_units(db_rows, _baseline):
    rows = [{"Id": r.get("id"), "UnitId": r["unit_id"], "TurretId": r["turret_id"],
             "Order": r.get("order", 0)} for r in db_rows]
    return _assign_ids(rows, [r.get("id") for r in db_rows])


def build_turret_weapons(db_rows, _baseline):
    rows = [{"Id": r.get("id"), "WeaponId": r["weapon_id"], "TurretId": r["turret_id"],
             "Order": r.get("order", 0), "WeaponChannel": r.get("channel", 0),
             "WeaponPriority": r.get("priority", 0)} for r in db_rows]
    return _assign_ids(rows, [r.get("id") for r in db_rows])


def build_squad_members(db_rows, baseline):
    by_id = {r["Id"]: r for r in baseline}
    out = []
    for r in db_rows:
        t = by_id.get(r["id"], {})
        special = r.get("special_weapon_id")
        if special is None:
            special = t.get("SpecialWeaponId", 0)
        out.append({
            "Id": r["id"],
            "DeathPriority": t.get("DeathPriority", 0),
            "ModelFileName": r.get("model") or t.get("ModelFileName"),
            "PrimaryWeaponId": r.get("primary_weapon_id"),
            "SpecialWeaponId": special,
            "UnitId": r["unit_id"],
        })
    return out


def build_squad_weapons(db_rows, _baseline):
    rows = [{"Id": r.get("id"), "WeaponId": r["weapon_id"], "UnitId": r["unit_id"]}
            for r in db_rows]
    return _assign_ids(rows, [r.get("id") for r in db_rows])


def build_weapon_ammunitions(db_rows, _baseline):
    rows = [{"Id": r.get("id"), "UnitId": r["unit_id"], "WeaponId": r["weapon_id"],
             "AmmunitionId": r["ammunition_id"], "Order": r.get("order", 0),
             "Quantity": r.get("quantity", 0)} for r in db_rows]
    return _assign_ids(rows, [r.get("id") for r in db_rows])


def build_passthrough(db_rows, _baseline):
    """Reference/bridge tables: write rows back verbatim (stored as-is)."""
    return [dict(r) for r in db_rows]


BUILDERS = {
    "units": build_units,
    "weapons": build_weapons,
    "ammunition": build_ammunition,
    "turrets": build_turrets,
    "turret_units": build_turret_units,
    "turret_weapons": build_turret_weapons,
    "squad_members": build_squad_members,
    "squad_weapons": build_squad_weapons,
    "weapon_ammunitions": build_weapon_ammunitions,
    "modifications": build_modifications,
    "options": build_options,
    "countries": build_passthrough,
    "specializations": build_passthrough,
    "specialization_availabilities": build_passthrough,
    "transport_availabilities": build_passthrough,
    "armors": build_passthrough,
    "unit_armors": build_passthrough,
    "mobility": build_passthrough,
    "unit_propulsions": build_passthrough,
    "fly_presets": build_passthrough,
    "sensors": build_passthrough,
    "sensor_units": build_passthrough,
    "abilities": build_passthrough,
    "unit_abilities": build_passthrough,
}
