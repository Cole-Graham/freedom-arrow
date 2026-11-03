namespace FreedomArrow;

static class Tables
{
    public static readonly (string Property, string File)[] All =
    {
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
    };

    public static readonly (string Source, string Field, string Target)[] Links =
    {
        ("weapon_ammunitions.json", "AmmunitionId", "ammunitions.json"),
        ("options.json", "ArmorId", "armors.json"),
        ("options.json", "MobilityId", "mobility.json"),
        ("squad_weapons.json", "WeaponId", "weapons.json"),
        ("unit_armors.json", "ArmorId", "armors.json"),
        ("unit_propulsions.json", "MobilityId", "mobility.json"),
        ("turret_units.json", "TurretId", "turrets.json"),
        ("turret_weapons.json", "TurretId", "turrets.json"),
        ("turret_weapons.json", "WeaponId", "weapons.json"),
        ("turrets.json", "ParentTurretId", "turrets.json"),
    };
}
