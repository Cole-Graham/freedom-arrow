"""Per-table field translation: game JSON (PascalCase, dense) -> db rows
(snake_case, sparse). Inverse of export/translate.py.

Only schema-declared fields are emitted; unknown JSON fields are dropped so
`db load` never rejects them.
"""
from __future__ import annotations

from typing import Any, Dict, List

# game JSON filename -> logical table
FILE_TABLE: Dict[str, str] = {
    "Units.json": "units",
    "WeaponsJson.json": "weapons",
    "AmmunitionsJson.json": "ammunition",
    "TurretsJson.json": "turrets",
    "TurretUnitsJson.json": "turret_units",
    "TurretWeaponsJson.json": "turret_weapons",
    "SquadMembersJson.json": "squad_members",
    "SquadWeaponsJson.json": "squad_weapons",
    "WeaponAmmunitionsJson.json": "weapon_ammunitions",
    "ModificationsJson.json": "modifications",
    "OptionsJson.json": "options",
    "CountriesJson.json": "countries",
    "SpecializationsJson.json": "specializations",
    "SpecializationAvailabilitiesJson.json": "specialization_availabilities",
    "TransportAvailabilitiesJson.json": "transport_availabilities",
    "ArmorsJson.json": "armors",
    "UnitArmorsJson.json": "unit_armors",
    "MobilityJson.json": "mobility",
    "UnitPropulsionsJson.json": "unit_propulsions",
    "FlyPresetsJson.json": "fly_presets",
    "SensorsJson.json": "sensors",
    "SensorUnitsJson.json": "sensor_units",
    "AbilitiesJson.json": "abilities",
    "UnitAbilitiesJson.json": "unit_abilities",
}

# tables stored verbatim (passthrough) - imported/exported without field mapping
PASSTHROUGH = {
    "countries", "specializations", "specialization_availabilities",
    "transport_availabilities", "armors", "unit_armors", "mobility",
    "unit_propulsions", "fly_presets", "sensors", "sensor_units",
    "abilities", "unit_abilities",
}
TABLE_FILE: Dict[str, str] = {v: k for k, v in FILE_TABLE.items()}

# straight scalar renames (JSON key -> db field); value copied when present
RENAME: Dict[str, Dict[str, str]] = {
    "units": {"Name": "name", "HUDName": "hud_name", "Cost": "cost",
              "Stealth": "stealth", "Type": "type", "Role": "role",
              "CategoryType": "category"},
    "weapons": {"Name": "name", "HUDName": "hud_name", "Type": "type"},
    "ammunition": {"Name": "name", "HUDName": "hud_name",
                   "TargetType": "target_type", "ArmorTargeted": "armor_targeted",
                   "TrajectoryType": "trajectory"},
    "turrets": {"Name": "name", "ParentTurretId": "parent_turret_id",
                "IsDefault": "is_default"},
    "modifications": {"UnitId": "unit_id", "UIName": "ui_name", "Type": "type",
                      "Order": "order", "ThumbnailFileName": "thumbnail"},
    "turret_units": {"UnitId": "unit_id", "TurretId": "turret_id", "Order": "order"},
    "turret_weapons": {"WeaponId": "weapon_id", "TurretId": "turret_id",
                       "Order": "order", "WeaponChannel": "channel",
                       "WeaponPriority": "priority"},
    "squad_members": {"UnitId": "unit_id", "PrimaryWeaponId": "primary_weapon_id",
                      "SpecialWeaponId": "special_weapon_id", "ModelFileName": "model"},
    "squad_weapons": {"UnitId": "unit_id", "WeaponId": "weapon_id"},
    "weapon_ammunitions": {"UnitId": "unit_id", "WeaponId": "weapon_id",
                           "AmmunitionId": "ammunition_id", "Order": "order",
                           "Quantity": "quantity"},
}

OPTION_SCALAR_INT = [
    ("ArmorId", "armor_id"), ("MobilityId", "mobility_id"),
    ("MainSensorId", "main_sensor_id"), ("ExtraSensorId", "extra_sensor_id"),
    ("ReplaceUnitId", "replace_unit_id"),
]
OPTION_SCALAR_FLOAT = [
    ("StealthOverride", "stealth_override"),
    ("TimeModifierRefund", "time_modifier_refund"),
    ("TimeModifierResurrect", "time_modifier_resurrect"),
]
OPTION_STRINGS = [
    ("ConcatenateWithUnitName", "concatenate_with_unit_name"),
    ("ReplaceUnitName", "replace_unit_name"),
    ("ThumbnailOverride", "thumbnail_override"),
    ("PortraitOverride", "portrait_override"),
    ("AudioPresetOverride", "audio_preset_override"),
]


def from_json_range(v: Any) -> float:
    """JSON half-range -> db real range. None->0; sentinels (<=0) preserved;
    else doubled."""
    if v is None:
        return 0.0
    f = float(v)
    if f <= 0.0:
        return f
    return f * 2.0


def _rename_row(table: str, jrow: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"id": jrow["Id"]}
    for jk, yk in RENAME[table].items():
        if jk in jrow and jrow[jk] is not None:
            out[yk] = jrow[jk]
    return out


def _ammunition_row(jrow: Dict[str, Any]) -> Dict[str, Any]:
    out = _rename_row("ammunition", jrow)
    ranges = {
        "ground": from_json_range(jrow.get("GroundRange")),
        "low_alt": from_json_range(jrow.get("LowAltRange")),
        "high_alt": from_json_range(jrow.get("HighAltRange")),
    }
    out["current"] = dict(ranges)
    out["vanilla"] = dict(ranges)
    out["real_world"] = {"ground": None, "low_alt": None, "high_alt": None}
    mr = jrow.get("MinimalRange")
    out["min_range"] = {"ground": float(mr) if mr is not None else 0.0}
    return out


def _option_row(jrow: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"id": jrow["Id"], "modification_id": jrow.get("ModificationId")}
    if jrow.get("UIName") is not None:
        out["ui_name"] = jrow["UIName"]
    if jrow.get("Order") is not None:
        out["order"] = jrow["Order"]
    if jrow.get("Cost") is not None:
        out["cost"] = jrow["Cost"]
    if jrow.get("OptionPicture"):
        out["option_picture"] = jrow["OptionPicture"]
    if jrow.get("IsDefault"):            # only when true
        out["is_default"] = True
    turret = {}
    for i in range(21):
        v = jrow.get(f"Turret{i}Id") or 0
        if v:
            turret[i] = v
    if turret:
        out["turret_overrides"] = turret
    ability = {}
    for i in (1, 2, 3):
        v = jrow.get(f"Ability{i}Id") or 0
        if v:
            ability[i] = v
    if ability:
        out["ability_overrides"] = ability
    for jk, yk in OPTION_SCALAR_INT:
        v = jrow.get(jk) or 0
        if v:
            out[yk] = v
    for jk, yk in OPTION_SCALAR_FLOAT:
        v = jrow.get(jk) or 0.0
        if v:
            out[yk] = float(v)
    for jk, yk in OPTION_STRINGS:
        v = jrow.get(jk)
        if v:
            out[yk] = v
    return out


def translate_table(table: str, jrows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if table in PASSTHROUGH:
        return [dict(r) for r in jrows]          # verbatim
    if table == "ammunition":
        return [_ammunition_row(r) for r in jrows]
    if table == "options":
        return [_option_row(r) for r in jrows]
    return [_rename_row(table, r) for r in jrows]
