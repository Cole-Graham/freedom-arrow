"""Broken Arrow DPM visualizer constants."""

from __future__ import annotations

# InfocardConfig.EffectiveRangeMultiplier. Card / targeting UI metres = world * 2.
CARD_RANGE_MULTIPLIER = 2.0
RANGE_STEP_CARD_M = 25.0

ARMOR_KINETIC = 1
ARMOR_HEAT = 2
ARMOR_IGNORE = 0

UNIT_TYPE_INFANTRY = 2

# Infantry hit box (InfantryConfig asset; InitInfantry / KillSquadSolders): a square of
# BaseSquadSize + 0.5 m per living soldier, Units.Height tall. Shells hit the box, not soldiers.
INFANTRY_BASE_SQUAD_SIZE = 1.0
INFANTRY_SIZE_PER_SOLDIER = 0.5

# WeaponType: RPGReloadable, RPGDisposable, ATGM, ATGMHE. Units-tab infantry DPM skips these.
INFANTRY_AT_WEAPON_TYPES = frozenset({62, 63, 80, 81})

# Armory slots that change weapons or armor. Pylons are omitted: their combinations explode.
LOADOUT_SLOT_UINAMES = frozenset(
    {
        "Custom_Slot_Weapon_package",
        "Custom_Slot_Squad_loadout",
        "Custom_Slot_Armor",
        "Custom_Slot_Ammunition",
        "Custom_Slot_Unit_variant",
        "Custom_Slot_Modernization",
        "Custom_Slot_Selfdefence_weapon",
        "Custom_Slot_Front_weapon",
        "Custom_Slot_Front_weapons",
        "Custom_Slot_Rear_weapon",
        "Custom_Slot_Rear_weapons",
        "Custom_Slot_Central_weapon",
        "Custom_Slot_Door_guns",
    }
)
MAX_LOADOUT_COMBINATIONS = 64

FACES = ("Front", "Sides", "Rear", "Top")
FACE_FIELDS = {
    "Front": ("KinArmorFront", "HeatArmorFront"),
    "Sides": ("KinArmorSides", "HeatArmorSides"),
    "Rear": ("KinArmorRear", "HeatArmorRear"),
    "Top": ("KinArmorTop", "HeatArmorTop"),
}

TABLE_FILES: tuple[tuple[str, str], ...] = (
    ("Units", "units.json"),
    ("AbilitiesJson", "abilities.json"),
    ("UnitAbilitiesJson", "unit_abilities.json"),
    ("AmmunitionsJson", "ammunitions.json"),
    ("ArmorsJson", "armors.json"),
    ("MobilityJson", "mobility.json"),
    ("FlyPresetsJson", "fly_presets.json"),
    ("UnitPropulsionsJson", "unit_propulsions.json"),
    ("CountriesJson", "countries.json"),
    ("TurretsJson", "turrets.json"),
    ("TurretUnitsJson", "turret_units.json"),
    ("WeaponsJson", "weapons.json"),
    ("TurretWeaponsJson", "turret_weapons.json"),
    ("WeaponAmmunitionsJson", "weapon_ammunitions.json"),
    ("SensorUnitsJson", "sensor_units.json"),
    ("SensorsJson", "sensors.json"),
    ("SquadMembersJson", "squad_members.json"),
    ("SquadWeaponsJson", "squad_weapons.json"),
    ("ModificationsJson", "modifications.json"),
    ("OptionsJson", "options.json"),
    ("UnitArmorsJson", "unit_armors.json"),
    ("SpecializationAvailabilitiesJson", "specialization_availabilities.json"),
    ("SpecializationsJson", "specializations.json"),
    ("TransportAvailabilitiesJson", "transport_availabilities.json"),
)

FIELD_TO_FILE = dict(TABLE_FILES)
FILE_TO_FIELD = {filename: field for field, filename in TABLE_FILES}
NEEDED_FIELDS = (
    "Units",
    "AmmunitionsJson",
    "ArmorsJson",
    "WeaponsJson",
    "WeaponAmmunitionsJson",
    "TurretsJson",
    "TurretUnitsJson",
    "TurretWeaponsJson",
    "SquadMembersJson",
    "SquadWeaponsJson",
    "ModificationsJson",
    "OptionsJson",
    "UnitArmorsJson",
    "CountriesJson",
)

LINE_COLORS = (
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
)

FACE_LINE_STYLES = {
    "Front": "-",
    "Sides": "--",
    "Rear": "-.",
    "Top": ":",
}


def format_dpm_y_axis_tick(value: float, _pos: int) -> str:
    """Format DPM axis ticks as plain numbers (no scientific notation)."""
    if value <= 0:
        return ""
    rounded = round(value)
    if abs(value - rounded) < max(1e-9, abs(value) * 1e-9):
        return str(int(rounded))
    if value >= 1:
        return str(int(round(value)))
    formatted = f"{value:.4g}"
    if "e" in formatted or "E" in formatted:
        formatted = f"{value:.4f}".rstrip("0").rstrip(".")
    return formatted or "0"
