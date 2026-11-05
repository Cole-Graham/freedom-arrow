"""Join units to weapons, ammunition, and armor."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .constants import FACE_FIELDS, FACES, INFANTRY_AT_WEAPON_TYPES, UNIT_TYPE_INFANTRY


@dataclass
class AmmoChoice:
    ammunition_id: int
    quantity: int
    order: int


@dataclass
class MountedWeapon:
    weapon_id: int
    gun_count: int
    ammos: list[AmmoChoice] = field(default_factory=list)
    default: bool = True


@dataclass
class ArmorOption:
    armor_id: int
    label: str
    is_default: bool
    option_id: int | None = None
    extra_cost: int = 0


class Catalog:
    def __init__(self, tables: dict[str, dict[int, dict[str, Any]]]):
        self.tables = tables
        self.units = tables["Units"]
        self.weapons = tables["WeaponsJson"]
        self.ammos = tables["AmmunitionsJson"]
        self.armors = tables["ArmorsJson"]
        self.countries = tables.get("CountriesJson", {})
        self._build_indexes()

    def _build_indexes(self) -> None:
        self.turrets_by_unit: dict[int, list[int]] = defaultdict(list)
        for row in self.tables["TurretUnitsJson"].values():
            self.turrets_by_unit[int(row["UnitId"])].append(int(row["TurretId"]))

        self.weapons_by_turret: dict[int, list[int]] = defaultdict(list)
        for row in self.tables["TurretWeaponsJson"].values():
            self.weapons_by_turret[int(row["TurretId"])].append(int(row["WeaponId"]))

        self.squad_weapons: dict[int, list[int]] = defaultdict(list)
        for row in self.tables["SquadWeaponsJson"].values():
            self.squad_weapons[int(row["UnitId"])].append(int(row["WeaponId"]))

        self.member_weapon_counts: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for row in self.tables["SquadMembersJson"].values():
            unit_id = int(row["UnitId"])
            for key in ("PrimaryWeaponId", "SpecialWeaponId"):
                weapon_id = int(row.get(key) or 0)
                if weapon_id:
                    self.member_weapon_counts[unit_id][weapon_id] += 1

        self.ammo_by_unit_weapon: dict[tuple[int, int], list[AmmoChoice]] = defaultdict(list)
        self.ammo_pairs: dict[tuple[int, int], AmmoChoice] = {}
        for row in self.tables["WeaponAmmunitionsJson"].values():
            unit_id = int(row["UnitId"])
            weapon_id = int(row["WeaponId"])
            choice = AmmoChoice(
                ammunition_id=int(row["AmmunitionId"]),
                quantity=int(row.get("Quantity") or 0),
                order=int(row.get("Order") or 0),
            )
            self.ammo_by_unit_weapon[(unit_id, weapon_id)].append(choice)
            self.ammo_pairs[(weapon_id, choice.ammunition_id)] = choice
        for choices in self.ammo_by_unit_weapon.values():
            choices.sort(key=lambda item: (item.order, item.ammunition_id))

        self.default_armor: dict[int, int] = {}
        self.unit_armor_ids: dict[int, list[int]] = defaultdict(list)
        for row in self.tables["UnitArmorsJson"].values():
            unit_id = int(row["UnitId"])
            armor_id = int(row["ArmorId"])
            self.unit_armor_ids[unit_id].append(armor_id)
            current = self.default_armor.get(unit_id)
            if current is None:
                self.default_armor[unit_id] = armor_id
            elif self.armors.get(armor_id, {}).get("IsDefault") and not self.armors.get(current, {}).get("IsDefault"):
                self.default_armor[unit_id] = armor_id

        self.mods_by_unit: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in self.tables["ModificationsJson"].values():
            self.mods_by_unit[int(row["UnitId"])].append(row)

        self.options_by_mod: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in self.tables["OptionsJson"].values():
            self.options_by_mod[int(row["ModificationId"])].append(row)

    def unit_label(self, unit_id: int) -> str:
        unit = self.units[unit_id]
        name = unit.get("HUDName") or unit.get("Name") or f"Unit {unit_id}"
        return f"{name} [{unit_id}]"

    def weapon_label(self, weapon_id: int) -> str:
        weapon = self.weapons.get(weapon_id, {})
        name = weapon.get("HUDName") or weapon.get("Name") or f"Weapon {weapon_id}"
        return f"{name} [{weapon_id}]"

    def ammo_label(self, ammunition_id: int) -> str:
        ammo = self.ammos.get(ammunition_id, {})
        name = ammo.get("HUDName") or ammo.get("Name") or f"Ammo {ammunition_id}"
        return f"{name} [{ammunition_id}]"

    def armor_label(self, armor_id: int) -> str:
        armor = self.armors.get(armor_id, {})
        name = armor.get("Name") or f"Armor {armor_id}"
        return f"{name} [{armor_id}]"

    def playable_units(self) -> list[int]:
        ids = [
            unit_id
            for unit_id, row in self.units.items()
            if row.get("DisplayInArmory", True) and not row.get("IsUnitModification")
        ]
        return sorted(ids, key=lambda uid: (self.unit_label(uid).lower(), uid))

    def default_weapon_ids(self, unit_id: int) -> list[int]:
        counts: dict[int, int] = defaultdict(int)
        for turret_id in self.turrets_by_unit.get(unit_id, []):
            for weapon_id in self.weapons_by_turret.get(turret_id, []):
                counts[weapon_id] += 1
        member_counts = self.member_weapon_counts.get(unit_id)
        if member_counts:
            for weapon_id, count in member_counts.items():
                counts[weapon_id] = max(counts.get(weapon_id, 0), count)
        elif unit_id in self.squad_weapons:
            for weapon_id in self.squad_weapons[unit_id]:
                counts[weapon_id] = max(counts.get(weapon_id, 0), 1)
        return sorted(counts, key=lambda weapon_id: (self.weapon_label(weapon_id).lower(), weapon_id))

    def is_infantry(self, unit_id: int) -> bool:
        unit = self.units.get(unit_id)
        return bool(unit) and int(unit.get("Type") or 0) == UNIT_TYPE_INFANTRY

    def is_anti_tank_weapon(self, weapon_id: int) -> bool:
        weapon = self.weapons.get(weapon_id)
        return bool(weapon) and int(weapon.get("Type") or 0) in INFANTRY_AT_WEAPON_TYPES

    def gun_count(self, unit_id: int, weapon_id: int) -> int:
        turret_count = 0
        for turret_id in self.turrets_by_unit.get(unit_id, []):
            turret_count += self.weapons_by_turret.get(turret_id, []).count(weapon_id)
        member_count = self.member_weapon_counts.get(unit_id, {}).get(weapon_id, 0)
        return max(turret_count, member_count, 1)

    def mounted_weapons(self, unit_id: int, include_upgrade: bool = False) -> list[MountedWeapon]:
        default_ids = set(self.default_weapon_ids(unit_id))
        weapon_ids = list(default_ids)
        if include_upgrade:
            extra = {
                weapon_id
                for (uid, weapon_id) in self.ammo_by_unit_weapon
                if uid == unit_id and weapon_id not in default_ids and weapon_id in self.weapons
            }
            weapon_ids.extend(sorted(extra))
        mounted: list[MountedWeapon] = []
        for weapon_id in weapon_ids:
            if weapon_id not in self.weapons:
                continue
            mounted.append(
                MountedWeapon(
                    weapon_id=weapon_id,
                    gun_count=self.gun_count(unit_id, weapon_id) if weapon_id in default_ids else 1,
                    ammos=list(self.ammo_by_unit_weapon.get((unit_id, weapon_id), [])),
                    default=weapon_id in default_ids,
                )
            )
        return mounted

    def dpm_weapons(self, unit_id: int, include_upgrade: bool = False) -> list[MountedWeapon]:
        """Default loadout for the Units tab. Infantry RPG/ATGM rows are omitted."""
        mounted = self.mounted_weapons(unit_id, include_upgrade=include_upgrade)
        if not self.is_infantry(unit_id):
            return mounted
        return [item for item in mounted if not self.is_anti_tank_weapon(item.weapon_id)]

    def pick_ammo(self, mounted: MountedWeapon, preference: str) -> AmmoChoice | None:
        if not mounted.ammos:
            return None
        if preference == "Kinetic":
            for choice in mounted.ammos:
                ammo = self.ammos.get(choice.ammunition_id, {})
                if int(ammo.get("ArmorTargeted") or 0) == 1:
                    return choice
        if preference == "HEAT":
            for choice in mounted.ammos:
                ammo = self.ammos.get(choice.ammunition_id, {})
                if int(ammo.get("ArmorTargeted") or 0) == 2:
                    return choice
        return mounted.ammos[0]

    def armor_options(self, unit_id: int) -> list[ArmorOption]:
        options: list[ArmorOption] = []
        seen: set[int] = set()
        default_id = self.default_armor.get(unit_id)
        if default_id:
            options.append(
                ArmorOption(
                    armor_id=default_id,
                    label=f"Default — {self.armor_label(default_id)}",
                    is_default=True,
                )
            )
            seen.add(default_id)
        for mod in self.mods_by_unit.get(unit_id, []):
            for option in self.options_by_mod.get(int(mod["Id"]), []):
                armor_id = int(option.get("ArmorId") or 0)
                if not armor_id or armor_id in seen:
                    continue
                seen.add(armor_id)
                name = option.get("Name") or option.get("UIName") or self.armor_label(armor_id)
                options.append(
                    ArmorOption(
                        armor_id=armor_id,
                        label=f"{name} — {self.armor_label(armor_id)}",
                        is_default=False,
                        option_id=int(option["Id"]),
                        extra_cost=int(option.get("Cost") or 0),
                    )
                )
        return options

    def weapon_ammo_labels(self) -> list[tuple[str, int, int]]:
        labels: list[tuple[str, int, int]] = []
        seen: set[tuple[int, int]] = set()
        for (unit_id, weapon_id), choices in self.ammo_by_unit_weapon.items():
            if weapon_id not in self.weapons:
                continue
            for choice in choices:
                key = (weapon_id, choice.ammunition_id)
                if key in seen or choice.ammunition_id not in self.ammos:
                    continue
                seen.add(key)
                label = f"{self.ammo_label(choice.ammunition_id)} — {self.weapon_label(weapon_id)}"
                labels.append((label, weapon_id, choice.ammunition_id))
        labels.sort(key=lambda item: item[0].lower())
        return labels

    def armor_labels(self) -> list[tuple[str, int]]:
        labels = [(self.armor_label(armor_id), armor_id) for armor_id in self.armors]
        labels.sort(key=lambda item: item[0].lower())
        return labels

    def silhouette(self, unit_id: int) -> tuple[float, float] | None:
        """GetTargetAccuracy target box: min(Length, Width) × Height, world metres."""
        unit = self.units.get(unit_id)
        if not unit:
            return None
        return (
            min(float(unit.get("Length") or 0), float(unit.get("Width") or 0)),
            float(unit.get("Height") or 0),
        )

    def silhouette_for_armor(self, armor_id: int) -> tuple[float, float] | None:
        for unit_id, default_id in self.default_armor.items():
            if default_id == armor_id:
                size = self.silhouette(unit_id)
                if size is not None:
                    return size
        return None

    def dummy_armor(self, face_values: dict[str, tuple[float, float]] | None = None, armor_value: float = 0, hp: float = 14) -> dict[str, Any]:
        row: dict[str, Any] = {
            "Id": 0,
            "Name": "Custom",
            "ArmorValue": armor_value,
            "MaxHealthPoints": hp,
        }
        for face in FACES:
            kin, heat = (0.0, 0.0) if not face_values else face_values.get(face, (0.0, 0.0))
            kin_field, heat_field = FACE_FIELDS[face]
            row[kin_field] = kin
            row[heat_field] = heat
        return row
