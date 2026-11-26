"""Join units to weapons, ammunition, and armor."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product
from typing import Any

from .constants import (
    FACE_FIELDS,
    FACES,
    INFANTRY_AT_WEAPON_TYPES,
    INFANTRY_BASE_SQUAD_SIZE,
    INFANTRY_SIZE_PER_SOLDIER,
    LOADOUT_SLOT_UINAMES,
    MAX_LOADOUT_COMBINATIONS,
    TARGET_TYPE_INFANTRY,
    UNIT_TYPE_INFANTRY,
)


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


@dataclass
class Loadout:
    label: str
    option_ids: tuple[int, ...]
    armor_id: int | None
    extra_cost: int
    turret_ids: tuple[int, ...]
    replace_unit_id: int | None
    is_default: bool


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
        self.squad_size: dict[int, int] = defaultdict(int)
        for row in self.tables["SquadMembersJson"].values():
            unit_id = int(row["UnitId"])
            self.squad_size[unit_id] += 1
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

        self.children_by_turret: dict[int, list[int]] = defaultdict(list)
        for turret_id, row in self.tables.get("TurretsJson", {}).items():
            parent = int(row.get("ParentTurretId") or 0)
            if parent:
                self.children_by_turret[parent].append(int(turret_id))

        self._loadouts: dict[int, list[Loadout]] = {}

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
        return self._weapon_ids_for_loadout(unit_id, self.default_loadout(unit_id))

    def is_infantry(self, unit_id: int) -> bool:
        unit = self.units.get(unit_id)
        return bool(unit) and int(unit.get("Type") or 0) == UNIT_TYPE_INFANTRY

    def is_anti_tank_weapon(self, weapon_id: int) -> bool:
        weapon = self.weapons.get(weapon_id)
        return bool(weapon) and int(weapon.get("Type") or 0) in INFANTRY_AT_WEAPON_TYPES

    def gun_count(self, unit_id: int, weapon_id: int, loadout: Loadout | None = None) -> int:
        effective_id, turret_ids = self._loadout_source(unit_id, loadout)
        turret_count = 0
        for turret_id in turret_ids:
            turret_count += self.weapons_by_turret.get(turret_id, []).count(weapon_id)
        member_count = self.member_weapon_counts.get(effective_id, {}).get(weapon_id, 0)
        return max(turret_count, member_count, 1)

    def mounted_weapons(
        self,
        unit_id: int,
        include_upgrade: bool = False,
        loadout: Loadout | None = None,
    ) -> list[MountedWeapon]:
        loadout = loadout or self.default_loadout(unit_id)
        effective_id, _turret_ids = self._loadout_source(unit_id, loadout)
        default_ids = set(self._weapon_ids_for_loadout(unit_id, loadout))
        weapon_ids = list(default_ids)
        if include_upgrade:
            extra = {
                weapon_id
                for (uid, weapon_id) in self.ammo_by_unit_weapon
                if uid == effective_id and weapon_id not in default_ids and weapon_id in self.weapons
            }
            weapon_ids.extend(sorted(extra))
        mounted: list[MountedWeapon] = []
        for weapon_id in weapon_ids:
            if weapon_id not in self.weapons:
                continue
            mounted.append(
                MountedWeapon(
                    weapon_id=weapon_id,
                    gun_count=self.gun_count(unit_id, weapon_id, loadout) if weapon_id in default_ids else 1,
                    ammos=list(self.ammo_by_unit_weapon.get((effective_id, weapon_id), [])),
                    default=weapon_id in default_ids,
                )
            )
        return mounted

    def dpm_weapons(
        self,
        unit_id: int,
        include_upgrade: bool = False,
        loadout: Loadout | None = None,
    ) -> list[MountedWeapon]:
        """Weapons for a loadout. An infantry RPG/ATGM keeps only the rounds that can target infantry
        (for example the M72A10's 66mm HE); with no such round it is omitted."""
        loadout = loadout or self.default_loadout(unit_id)
        mounted = self.mounted_weapons(unit_id, include_upgrade=include_upgrade, loadout=loadout)
        effective_id, _ = self._loadout_source(unit_id, loadout)
        if not self.is_infantry(effective_id):
            return mounted
        kept = []
        for item in mounted:
            if self.is_anti_tank_weapon(item.weapon_id):
                item.ammos = [choice for choice in item.ammos if self.can_target_infantry(choice.ammunition_id)]
                if not item.ammos:
                    continue
            kept.append(item)
        return kept

    def can_target_infantry(self, ammunition_id: int) -> bool:
        return bool(int(self.ammos.get(ammunition_id, {}).get("TargetType") or 0) & TARGET_TYPE_INFANTRY)

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

    def loadouts(self, unit_id: int) -> list[Loadout]:
        cached = self._loadouts.get(unit_id)
        if cached is not None:
            return cached
        mods = self._loadout_mods(unit_id)
        if not mods:
            result = [self._stock_loadout(unit_id)]
            self._loadouts[unit_id] = result
            return result
        slots = [self._slot_options(mod) for mod in mods]
        default_opts = tuple(self._default_option(opts) for opts in slots)
        combos = self._loadout_combinations(slots, default_opts)
        result: list[Loadout] = []
        used_labels: set[str] = set()
        for options in combos:
            loadout = self._loadout_from_options(unit_id, options, options == default_opts)
            label = loadout.label
            if label in used_labels:
                label = f"{label} [{','.join(str(oid) for oid in loadout.option_ids)}]"
                loadout = Loadout(
                    label=label,
                    option_ids=loadout.option_ids,
                    armor_id=loadout.armor_id,
                    extra_cost=loadout.extra_cost,
                    turret_ids=loadout.turret_ids,
                    replace_unit_id=loadout.replace_unit_id,
                    is_default=loadout.is_default,
                )
            used_labels.add(loadout.label)
            result.append(loadout)
        result.sort(key=lambda item: (not item.is_default, item.label.lower()))
        self._loadouts[unit_id] = result
        return result

    def default_loadout(self, unit_id: int) -> Loadout:
        for loadout in self.loadouts(unit_id):
            if loadout.is_default:
                return loadout
        loadouts = self.loadouts(unit_id)
        return loadouts[0] if loadouts else self._stock_loadout(unit_id)

    def loadout_by_label(self, unit_id: int, label: str) -> Loadout | None:
        wanted = (label or "").strip()
        if not wanted:
            return None
        for loadout in self.loadouts(unit_id):
            if loadout.label == wanted:
                return loadout
        return None

    def loadout_labels(self, unit_id: int) -> list[str]:
        return [loadout.label for loadout in self.loadouts(unit_id)]

    def _loadout_mods(self, unit_id: int) -> list[dict[str, Any]]:
        mods = [
            mod
            for mod in self.mods_by_unit.get(unit_id, [])
            if (mod.get("UIName") or "") in LOADOUT_SLOT_UINAMES and self._slot_options(mod)
        ]
        mods.sort(key=lambda mod: (int(mod.get("Order") or 0), int(mod["Id"])))
        return mods

    def _slot_options(self, mod: dict[str, Any]) -> list[dict[str, Any]]:
        options = list(self.options_by_mod.get(int(mod["Id"]), []))
        options.sort(key=lambda option: (int(option.get("Order") or 0), int(option["Id"])))
        return options

    def _default_option(self, options: list[dict[str, Any]]) -> dict[str, Any]:
        for option in options:
            if option.get("IsDefault"):
                return option
        return options[0]

    def _loadout_combinations(
        self,
        slots: list[list[dict[str, Any]]],
        default_opts: tuple[dict[str, Any], ...],
    ) -> list[tuple[dict[str, Any], ...]]:
        total = 1
        for slot in slots:
            total *= max(1, len(slot))
        if total <= MAX_LOADOUT_COMBINATIONS:
            return [tuple(combo) for combo in product(*slots)]
        combos = [default_opts]
        seen = {tuple(int(option["Id"]) for option in default_opts)}
        for index, slot in enumerate(slots):
            for option in slot:
                row = list(default_opts)
                row[index] = option
                key = tuple(int(item["Id"]) for item in row)
                if key not in seen:
                    seen.add(key)
                    combos.append(tuple(row))
        return combos

    def _option_short_name(self, option: dict[str, Any]) -> str:
        ui = str(option.get("UIName") or "")
        name = str(option.get("Name") or "")
        if ui and not ui.startswith("Custom_Option") and not ui.startswith("dlc_"):
            return ui
        for prefix in ("Custom_Option_", "dlc_3_Custom_Option_"):
            if ui.startswith(prefix):
                return ui[len(prefix) :].replace("_", " ").strip() or name or ui
        return name or ui or f"Option {option.get('Id')}"

    def _combo_label(self, options: list[dict[str, Any]], is_default: bool) -> str:
        parts = []
        for option in options:
            short = self._option_short_name(option)
            if short.lower() == "default" and len(options) > 1:
                continue
            parts.append(short)
        text = " / ".join(parts) if parts else "Default"
        if is_default and not text.lower().startswith("default"):
            return f"Default — {text}"
        return text

    def _turrets_from_option(self, option: dict[str, Any]) -> list[int]:
        turrets: list[int] = []
        for index in range(21):
            turret_id = int(option.get(f"Turret{index}Id") or 0)
            if turret_id:
                turrets.append(turret_id)
        return turrets

    def _expand_turrets(self, turret_ids: list[int]) -> tuple[int, ...]:
        out: list[int] = []
        seen: set[int] = set()
        for turret_id in turret_ids:
            for item in (turret_id, *self.children_by_turret.get(turret_id, [])):
                if item not in seen:
                    seen.add(item)
                    out.append(item)
        return tuple(out)

    def _stock_turret_ids(self, unit_id: int) -> tuple[int, ...]:
        declared = [
            turret_id
            for turret_id in self.turrets_by_unit.get(unit_id, [])
            if self.tables.get("TurretsJson", {}).get(turret_id, {}).get("IsDefault")
        ]
        if not declared:
            for mod in self._loadout_mods(unit_id):
                option = self._default_option(self._slot_options(mod))
                declared.extend(self._turrets_from_option(option))
        if not declared:
            declared = list(self.turrets_by_unit.get(unit_id, []))
        return self._expand_turrets(declared)

    def _stock_loadout(self, unit_id: int) -> Loadout:
        return Loadout(
            label="Default",
            option_ids=(),
            armor_id=self.default_armor.get(unit_id),
            extra_cost=0,
            turret_ids=self._stock_turret_ids(unit_id),
            replace_unit_id=None,
            is_default=True,
        )

    def _loadout_from_options(
        self,
        unit_id: int,
        options: tuple[dict[str, Any], ...],
        is_default: bool,
    ) -> Loadout:
        extra = 0
        armor_id: int | None = None
        replace_id: int | None = None
        turrets: list[int] = []
        for option in options:
            extra += int(option.get("Cost") or 0)
            option_armor = int(option.get("ArmorId") or 0)
            if option_armor:
                armor_id = option_armor
            replaced = int(option.get("ReplaceUnitId") or 0)
            if replaced:
                replace_id = replaced
            turrets.extend(self._turrets_from_option(option))
        source_id = replace_id if replace_id and replace_id in self.units else unit_id
        if not armor_id:
            armor_id = self.default_armor.get(source_id)
        turret_ids = self._expand_turrets(turrets)
        if not turret_ids:
            turret_ids = self._stock_turret_ids(source_id)
        return Loadout(
            label=self._combo_label(list(options), is_default),
            option_ids=tuple(int(option["Id"]) for option in options),
            armor_id=armor_id,
            extra_cost=extra,
            turret_ids=turret_ids,
            replace_unit_id=replace_id if replace_id and replace_id != unit_id else None,
            is_default=is_default,
        )

    def _loadout_source(self, unit_id: int, loadout: Loadout | None) -> tuple[int, tuple[int, ...]]:
        loadout = loadout or self.default_loadout(unit_id)
        effective_id = loadout.replace_unit_id or unit_id
        turret_ids = loadout.turret_ids or self._stock_turret_ids(effective_id)
        return effective_id, turret_ids

    def _weapon_ids_for_loadout(self, unit_id: int, loadout: Loadout) -> list[int]:
        effective_id, turret_ids = self._loadout_source(unit_id, loadout)
        counts: dict[int, int] = defaultdict(int)
        for turret_id in turret_ids:
            for weapon_id in self.weapons_by_turret.get(turret_id, []):
                counts[weapon_id] += 1
        member_counts = self.member_weapon_counts.get(effective_id)
        if member_counts:
            for weapon_id, count in member_counts.items():
                counts[weapon_id] = max(counts.get(weapon_id, 0), count)
        elif effective_id in self.squad_weapons and not counts:
            for weapon_id in self.squad_weapons[effective_id]:
                counts[weapon_id] = max(counts.get(weapon_id, 0), 1)
        return sorted(counts, key=lambda weapon_id: (self.weapon_label(weapon_id).lower(), weapon_id))

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

    def weapon_ammo_entries(self) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Weapon + round list with stats (Lateralus 26 Nov 2026: many rows share one name; same as the website).

        Each entry: label "ammo [ids] — weapon [ids] · dmg · range · pen · tier · N units", weapon_id, ammo_id, live (carried by a
        unit that can be in a deck: playable or an option's replacement unit) and tip (the unit names). Rows whose stats are the same
        apart from strings, SupplyCost and ResupplyTime are one entry. Also returns old label ("ammo [id] — weapon [id]") -> new label.
        """
        from .calculations import card_range_text

        in_game = set(self.playable_units())
        for unit_id in list(in_game):  # loadout units a playable card swaps to (e.g. Marine Raiders CQC)
            for mod in self.mods_by_unit.get(unit_id, []):
                for option in self.options_by_mod.get(int(mod["Id"]), []):
                    replace = int(option.get("ReplaceUnitId") or 0)
                    if replace:
                        in_game.add(replace)
        users: dict[tuple[int, int], set[int]] = defaultdict(set)
        for (unit_id, weapon_id), choices in self.ammo_by_unit_weapon.items():
            carried = self.member_weapon_counts.get(unit_id)
            if carried and weapon_id not in carried:  # vanilla keeps ammo rows for weapons no soldier has (Spetsnaz Alpha RPL-7)
                continue
            for choice in choices:
                users[(weapon_id, choice.ammunition_id)].add(unit_id)

        def sig(row: dict[str, Any], skip: set[str]) -> str:
            # Numbers compared as floats (10 == 10.0), as the website does.
            return repr(sorted((k, float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                               for k, v in row.items() if k not in skip and not isinstance(v, str)))

        skip_w, skip_a = {"Id", "_v"}, {"Id", "_v", "SupplyCost", "ResupplyTime"}
        groups: dict[tuple[str, str, str, str], list[tuple[int, int]]] = defaultdict(list)
        for _label, weapon_id, ammo_id in self.weapon_ammo_labels():
            weapon, ammo = self.weapons[weapon_id], self.ammos[ammo_id]
            key = (str(ammo.get("HUDName") or ammo.get("Name")), str(weapon.get("HUDName") or weapon.get("Name")), sig(weapon, skip_w), sig(ammo, skip_a))
            groups[key].append((weapon_id, ammo_id))
        # Lateralus 26 Nov 2026: entries that share a name show only what differs between them; an entry with no look-alike shows
        # damage, range, penetration and magazine. Same items and wording as the website.
        def num(v: Any) -> str:
            v = float(v or 0)
            return f"{v:.1f}" if v.is_integer() else repr(v)

        def rng(a: Any, b: Any, unit: str = "") -> str:
            return f"{num(a)}{unit}" if num(a) == num(b) else f"{num(a)}–{num(b)}{unit}"

        def pen(w: dict, a: dict) -> str:
            lo, hi = float(a.get("PenetrationAtMinRange") or 0), float(a.get("PenetrationAtGroundRange") or 0)
            return "" if not lo and not hi else f"pen {num(lo)}" if lo == hi else f"pen {num(lo)}→{num(hi)}"

        def tier(w: dict, a: dict) -> str:
            m = re.search(r"\bT(\d)\b", str(a.get("Name") or ""))
            return f"T{m.group(1)}" if m else ""

        items = [
            ("dmg", lambda w, a: f"dmg {num(a.get('Damage'))}"),
            ("range", lambda w, a: card_range_text(a).replace("range ", "", 1).strip()),
            ("pen", pen),
            ("mag", lambda w, a: f"mag {int(float(w.get('MagazineSize') or 0))}"),
            ("reload", lambda w, a: f"reload {rng(w.get('MagazineReloadTimeMin'), w.get('MagazineReloadTimeMax'), ' s')}"),
            ("burst", lambda w, a: f"burst {rng(w.get('ShotsPerBurstMin'), w.get('ShotsPerBurstMax'))} every "
                                   f"{rng(w.get('TimeBetweenBurstsMin'), w.get('TimeBetweenBurstsMax'), ' s')}"),
            ("gap", lambda w, a: f"shot gap {num(w.get('TimeBetweenShotsInBurst'))} s"),
            ("aim", lambda w, a: f"aim {rng(w.get('AimTimeMin'), w.get('AimTimeMax'), ' s')}"),
            ("spread", lambda w, a: f"spread {num(a.get('DispersionHorizontalRadius'))}×{num(a.get('DispersionVerticalRadius'))}"),
            ("stress", lambda w, a: f"stress {num(a.get('StressDamage'))}"),
            ("blast", lambda w, a: f"blast {num(a.get('HealthAOERadius'))}"),
            ("cover", lambda w, a: f"ignores cover {num(a.get('IgnoreCover'))}"),
            ("targets", lambda w, a: f"targets {int(float(a.get('TargetType') or 0))}"),
            ("move", lambda w, a: "fires on the move" if w.get("CanShootOnTheMove") else "no fire on the move"),
            ("tier", tier),
        ]
        base = {"dmg", "range", "pen", "mag", "tier"}
        raw_names = {"LowerVerticalAngle": "gun depression", "UpperVerticalAngles": "gun elevation", "VerticalRotationSpeed": "elevation speed",
                     "ShortGroundAttackBurst": "ground-attack bursts", "NormalGroundAttackBurst": "ground-attack bursts",
                     "LongGroundAttackBurst": "ground-attack bursts", "Type": "weapon type", "CanBeMerged": "merge flag",
                     "FlashPerShot": "muzzle flash", "HasPriorityOnChassis": "hull priority", "MuzzleVelocity": "muzzle velocity",
                     "VfxCountPerShotMax": "effects", "VfxCountPerShot": "effects", "HUDMultiplier": "card ammo multiplier"}
        ents: list[dict[str, Any]] = []
        for members in groups.values():
            weapon_id, ammo_id = min(members, key=lambda m: (m[1], m[0]))
            weapon, ammo = self.weapons[weapon_id], self.ammos[ammo_id]
            carriers = set().union(*(users.get(m, set()) for m in members))
            ents.append({"members": members, "weapon_ids": sorted({w for w, _ in members}), "ammo_ids": sorted({a for _, a in members}),
                         "weapon_id": weapon_id, "ammo_id": ammo_id, "weapon": weapon, "ammo": ammo, "carriers": carriers,
                         "live": sorted(u for u in carriers if u in in_game),
                         "name": (str(ammo.get("HUDName") or ammo.get("Name")), str(weapon.get("HUDName") or weapon.get("Name"))),
                         "vals": [fn(weapon, ammo) for _, fn in items]})
        siblings: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for e in ents:
            siblings[e["name"]].append(e)
        skip_raw = {"Id", "_v", "Name", "SupplyCost", "ResupplyTime"}
        entries: list[dict[str, Any]] = []
        aliases: dict[str, str] = {}
        for e in ents:
            others = siblings[e["name"]]
            if len(others) > 1:
                bits = [e["vals"][i] for i in range(len(items)) if len({o["vals"][i] for o in others}) > 1 and e["vals"][i]]
                if not bits:
                    raw = []
                    for src in ("weapon", "ammo"):
                        for k in sorted(set().union(*(o[src].keys() for o in others)) - skip_raw):
                            if len({repr(o[src].get(k)) for o in others}) > 1 and not any(isinstance(o[src].get(k), str) for o in others):
                                name = raw_names.get(k, k)
                                if name not in raw:
                                    raw.append(name)
                    bits = ["differs in " + ", ".join(raw[:3]) if raw else "same stats"]
            else:
                bits = [e["vals"][i] for i, (key, _) in enumerate(items) if key in base and e["vals"][i]]
            live = e["live"]
            bits.append(f"{len(live)} unit{'' if len(live) == 1 else 's'}" if live else "not in any deck")
            ammo, weapon = e["ammo"], e["weapon"]
            label = (f"{ammo.get('HUDName') or ammo.get('Name')} [{'/'.join(map(str, e['ammo_ids']))}] — "
                     f"{weapon.get('HUDName') or weapon.get('Name')} [{'/'.join(map(str, e['weapon_ids']))}] · " + " · ".join(b for b in bits if b))
            names = sorted((self.unit_label(u) if u in self.units else f"unit {u}") for u in (live or sorted(e["carriers"])))
            tip = ", ".join(names) + (f"  ·  same stats except supply: ammo {', '.join(map(str, e['ammo_ids']))}" if len(e["ammo_ids"]) > 1 else "")
            entries.append({"label": label, "weapon_id": e["weapon_id"], "ammo_id": e["ammo_id"], "live": bool(live), "tip": tip})
            for w, a in e["members"]:
                aliases[f"{self.ammo_label(a)} — {self.weapon_label(w)}"] = label
            aliases[label.split(" · ")[0]] = label
        entries.sort(key=lambda e: e["label"].lower())
        return entries, aliases

    # Infantry armor rows are named "<class> <N>Men" (for example "Armor Infantry Elite 7Men").
    # Every row of a class has the same armor; health is 5 per soldier.
    _INFANTRY_ROW = re.compile(r"^(Armor Infantry.*?)\s*(\d+)\s*Men$")
    HP_PER_SOLDIER = 5

    def infantry_armor_classes(self) -> dict[str, dict[int, int]]:
        """{class name: {men: armor id}} for the infantry armor rows."""
        classes: dict[str, dict[int, int]] = defaultdict(dict)
        for armor_id, armor in self.armors.items():
            match = self._INFANTRY_ROW.match((armor.get("Name") or "").strip())
            if match:
                classes[match.group(1).strip()][int(match.group(2))] = armor_id
        return dict(classes)

    def armor_menu_labels(self) -> list[str]:
        """Armor rows for the menus: one entry per infantry class (men picked separately), then every other row."""
        classes = self.infantry_armor_classes()
        grouped = {armor_id for rows in classes.values() for armor_id in rows.values()}
        others = [label for label, armor_id in self.armor_labels() if armor_id not in grouped]
        return sorted(classes) + others

    def infantry_armor(self, class_name: str, men: int) -> tuple[dict[str, Any], tuple[float, float] | None]:
        """Armor and hit box for any number of men of an infantry class, even a count with no row in the game.

        Armor values come from the class's nearest row; health is 5 per soldier; the box is the game's squad box.
        """
        rows = self.infantry_armor_classes()[class_name]
        nearest = min(rows, key=lambda count: (abs(count - men), count))
        armor = dict(self.armors[rows[nearest]])
        armor["MaxHealthPoints"] = float(self.HP_PER_SOLDIER * men)
        armor["Name"] = f"{class_name} {men}Men"
        if men not in rows:
            armor["Id"] = 0
        size = self.silhouette_for_armor(rows[nearest])
        box = (INFANTRY_BASE_SQUAD_SIZE + INFANTRY_SIZE_PER_SOLDIER * men, size[1]) if size else None
        return armor, box

    def split_infantry_label(self, label: str) -> tuple[str, int] | None:
        """Turn an old saved row label such as "Armor Infantry 8Men [84]" into (class, men)."""
        name = label.rsplit(" [", 1)[0].strip()
        match = self._INFANTRY_ROW.match(name)
        return (match.group(1).strip(), int(match.group(2))) if match else None

    def armor_labels(self) -> list[tuple[str, int]]:
        labels = [(self.armor_label(armor_id), armor_id) for armor_id in self.armors]
        labels.sort(key=lambda item: item[0].lower())
        return labels

    def silhouette(self, unit_id: int) -> tuple[float, float] | None:
        """Target box the shell must pass through: (width, height), world metres.

        Infantry: HitDetectionSystem.GetUnitBox uses InfantryUnitComponent.CurrentSquadSize,
        which is 1 + 0.5 per soldier (full squad here). Vehicles: min(Length, Width) × Height.
        """
        unit = self.units.get(unit_id)
        if not unit:
            return None
        height = float(unit.get("Height") or 0)
        soldiers = self.squad_size.get(unit_id, 0)
        if soldiers:
            return (INFANTRY_BASE_SQUAD_SIZE + INFANTRY_SIZE_PER_SOLDIER * soldiers, height)
        return (
            min(float(unit.get("Length") or 0), float(unit.get("Width") or 0)),
            height,
        )

    def silhouette_for_armor(self, armor_id: int) -> tuple[float, float] | None:
        """Target box for a plate set. Default wearers first, then any unit that can mount the kit."""
        candidates: list[tuple[int, int]] = []
        for unit_id, default_id in self.default_armor.items():
            if default_id == armor_id:
                candidates.append((0, unit_id))
        for unit_id, armor_ids in self.unit_armor_ids.items():
            if armor_id in armor_ids:
                candidates.append((1, unit_id))
        playable = set(self.playable_units())
        candidates.sort(key=lambda item: (item[0], 0 if item[1] in playable else 1, item[1]))
        for _rank, unit_id in candidates:
            size = self.silhouette(unit_id)
            if size is not None and size[0] > 0 and size[1] > 0:
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
