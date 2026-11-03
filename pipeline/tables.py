"""The 24 DataBaseCompiled string fields and their constants filenames.

Field order matches thirdparty-tools/BodkinToolkit/extractor/crypto.py.
Filenames are the authored files under mod/constants/.
"""

from __future__ import annotations

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

FIELD_ORDER: tuple[str, ...] = tuple(field for field, _filename in TABLE_FILES)
FIELD_TO_FILE: dict[str, str] = dict(TABLE_FILES)
FILE_TO_FIELD: dict[str, str] = {filename: field for field, filename in TABLE_FILES}

OBJECT_NAME = "DataBaseCompiled"
