"""Hit damage, penetration falloff, RoF, and DPM vs range."""

from __future__ import annotations

import math
from typing import Any, Iterable

from .constants import (
    ARMOR_HEAT,
    ARMOR_IGNORE,
    ARMOR_KINETIC,
    CARD_RANGE_MULTIPLIER,
    FACE_FIELDS,
    RANGE_STEP_CARD_M,
)


def _mid(lo: float, hi: float) -> float:
    return (float(lo) + float(hi)) / 2.0


def damage_formula_heat(base_damage: float, penetration: float, armor: float) -> float:
    """BattleSystemHelpers.DamageFormulaHEAT: share = r^2 / (1 + r^2)."""
    if armor <= 0:
        return float(base_damage)
    r2 = float(penetration) * float(penetration)
    a2 = float(armor) * float(armor)
    return float(base_damage) * r2 / (r2 + a2)


def damage_formula_kinetic(base_damage: float, penetration: float, armor: float) -> float:
    """BattleSystemHelpers.DamageFormulaKinetic.

    r = pen / armor. Full damage at r >= 1. Zero at r <= 0.5. Otherwise
    share = max(0.1, 2 - 1/r).
    """
    if armor <= 0:
        return float(base_damage)
    if penetration <= 0:
        return 0.0
    ratio = float(penetration) / float(armor)
    if ratio >= 1.0:
        return float(base_damage)
    if ratio <= 0.5:
        return 0.0
    return float(base_damage) * max(0.1, 2.0 - 1.0 / ratio)


def uses_value_armor(armor: dict[str, Any]) -> bool:
    """Infantry / helicopter / some planes: ArmorValue, HEAT curve for every round."""
    return float(armor.get("ArmorValue") or 0) > 0


def face_armor(armor: dict[str, Any], face: str, armor_targeted: int) -> float:
    if uses_value_armor(armor):
        return float(armor.get("ArmorValue") or 0)
    kin_field, heat_field = FACE_FIELDS[face]
    if armor_targeted == ARMOR_HEAT:
        return float(armor.get(heat_field) or 0)
    return float(armor.get(kin_field) or 0)


def penetration_at_range(ammo: dict[str, Any], world_m: float) -> float:
    """Linear falloff from point-blank to GroundRange. Min range is a fire gate, not the curve."""
    pen_min = float(ammo.get("PenetrationAtMinRange") or 0)
    pen_ground = float(ammo.get("PenetrationAtGroundRange") or 0)
    ground = float(ammo.get("GroundRange") or 0)
    if ground <= 0:
        return pen_ground
    if world_m <= 0:
        return pen_min
    if world_m >= ground:
        return pen_ground
    t = world_m / ground
    return pen_min + t * (pen_ground - pen_min)


def hit_damage(
    ammo: dict[str, Any],
    armor: dict[str, Any],
    world_m: float,
    face: str,
    damage_type: str = "Physical",
) -> float:
    """Post-armor HP damage, or stress with no armor ratio. Hits are assumed."""
    if damage_type == "Stress":
        return float(ammo.get("StressDamage") or 0)
    base = float(ammo.get("Damage") or 0)
    targeted = int(ammo.get("ArmorTargeted") or 0)
    if targeted == ARMOR_IGNORE:
        return base
    pen = penetration_at_range(ammo, world_m)
    plate = face_armor(armor, face, targeted)
    if uses_value_armor(armor) or targeted == ARMOR_HEAT:
        return damage_formula_heat(base, pen, plate)
    return damage_formula_kinetic(base, pen, plate)


def rate_of_fire_second(
    weapon: dict[str, Any],
    gun_count: float = 1.0,
    time_between_bursts_modifier: float = 1.0,
    magazine_reload_time_modifier: float = 1.0,
) -> float:
    """WeaponHelper.RateOfFireSecond: sustained shots per second for gun_count copies."""
    magazine = max(1.0, float(weapon.get("MagazineSize") or 1))
    burst = _mid(weapon.get("ShotsPerBurstMin") or 0, weapon.get("ShotsPerBurstMax") or 0)
    if burst < 1:
        burst = 1.0
    time_in_burst_gap = float(weapon.get("TimeBetweenShotsInBurst") or 0)
    time_between_bursts = _mid(
        weapon.get("TimeBetweenBurstsMin") or 0,
        weapon.get("TimeBetweenBurstsMax") or 0,
    ) * time_between_bursts_modifier
    reload = _mid(
        weapon.get("MagazineReloadTimeMin") or 0,
        weapon.get("MagazineReloadTimeMax") or 0,
    ) * magazine_reload_time_modifier
    bursts = magazine / burst
    intra_gaps = max(0.0, magazine - bursts)
    inter_gaps = max(0.0, bursts - 1.0)
    cycle = intra_gaps * time_in_burst_gap + inter_gaps * time_between_bursts + reload
    if cycle <= 0:
        per_shot = time_in_burst_gap or time_between_bursts
        if per_shot <= 0:
            return 0.0
        return float(gun_count) / per_shot
    return float(gun_count) * magazine / cycle


def shots_per_minute(weapon: dict[str, Any], gun_count: float = 1.0) -> float:
    return rate_of_fire_second(weapon, gun_count) * 60.0


def in_range(ammo: dict[str, Any], world_m: float) -> bool:
    ground = float(ammo.get("GroundRange") or 0)
    minimum = float(ammo.get("MinimalRange") or 0)
    if ground <= 0:
        return False
    return minimum <= world_m <= ground


def _card_m(world_m: float) -> float:
    return float(world_m) * CARD_RANGE_MULTIPLIER


def card_range_text(ammo: dict[str, Any]) -> str:
    """Pin-panel range in card metres (table world range × 2)."""
    minimum = _card_m(ammo.get("MinimalRange") or 0)
    ground = _card_m(ammo.get("GroundRange") or 0)
    low = _card_m(ammo.get("LowAltRange") or 0)
    high = _card_m(ammo.get("HighAltRange") or 0)
    parts: list[str] = []
    if ground > 0:
        if minimum > 0:
            parts.append(f"{minimum:.0f}–{ground:.0f}")
        else:
            parts.append(f"0–{ground:.0f}")
    if low > 0:
        parts.append(f"low {low:.0f}")
    if high > 0 and abs(high - low) > 0.5:
        parts.append(f"high {high:.0f}")
    if not parts:
        return ""
    return "range " + "  ".join(parts) + " card m"


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def dispersion_reference_range(ammo: dict[str, Any]) -> float:
    """Ammunitions.GetDispersionReferenceRange: first positive Ground / LowAlt / HighAlt."""
    for key in ("GroundRange", "LowAltRange", "HighAltRange"):
        value = float(ammo.get(key) or 0)
        if value > 0:
            return value
    return 1.0


def hit_chance(
    ammo: dict[str, Any],
    world_m: float,
    silhouette: tuple[float, float] | None = None,
) -> float:
    """Share of unguided rounds that pass through the target box.

    Seekers return DispersionHorizontalRadius (missile accuracy). Unguided rounds
    scale H×V spread by range. ShootingSystem.AddBallisticDeviation spreads rounds
    over a diamond |x|/rx + |y|/ry <= 1 (see diamond_in_box); the round hits if it
    lands inside the width × height box, centred on the aim point.
    """
    if int(ammo.get("Seeker") or 0) != 0:
        return float(ammo.get("DispersionHorizontalRadius") or 0)
    reference = dispersion_reference_range(ammo)
    ratio = 0.0 if reference <= 0 else world_m / reference
    spread_t = _clamp01(ratio)
    spread_min = float(ammo.get("DispersionMinimal") or 0)
    scale = _clamp01(spread_min + (1.0 - spread_min) * spread_t)
    radius_x = scale * float(ammo.get("DispersionHorizontalRadius") or 0)
    radius_y = scale * float(ammo.get("DispersionVerticalRadius") or 0)
    if silhouette is None:
        return 1.0
    width, height = silhouette
    return diamond_in_box(radius_x, radius_y, width, height)


def diamond_in_box(radius_x: float, radius_y: float, width: float, height: float) -> float:
    """Share of rounds inside a width × height box centred on the aim point.

    AddBallisticDeviation draws u evenly in [-1, 1], then v evenly in [-(1 - |u|), 1 - |u|],
    and offsets the round by (u × radius_x, v × radius_y). The spread is diamond-shaped,
    with more rounds near the left and right tips than an even fill.
    """
    if width <= 0 or height <= 0:
        return 0.0
    p = 1.0 if radius_x <= 0 else min(1.0, width / (2.0 * radius_x))
    q = 1.0 if radius_y <= 0 else min(1.0, height / (2.0 * radius_y))
    if radius_x <= 0:
        # u is always 0, so v is even over [-1, 1].
        return q
    # Hit share = integral over |u| in [0, p] of min(1, q / (1 - |u|)).
    knee = 1.0 - q
    if p <= knee:
        return _clamp01(-q * math.log(1.0 - p))
    return _clamp01(-q * math.log(q) + (p - knee))


def dpm_at_world(
    weapon: dict[str, Any],
    ammo: dict[str, Any],
    armor: dict[str, Any],
    world_m: float,
    face: str,
    gun_count: float = 1.0,
    damage_type: str = "Physical",
    silhouette: tuple[float, float] | None = None,
    apply_accuracy: bool = False,
) -> float:
    if not in_range(ammo, world_m):
        return 0.0
    damage = hit_damage(ammo, armor, world_m, face, damage_type)
    chance = hit_chance(ammo, world_m, silhouette) if apply_accuracy else 1.0
    return damage * chance * shots_per_minute(weapon, gun_count)


def sample_dpm(
    weapon: dict[str, Any],
    ammo: dict[str, Any],
    armor: dict[str, Any],
    face: str,
    gun_count: float = 1.0,
    damage_type: str = "Physical",
    range_step_card: float = RANGE_STEP_CARD_M,
    silhouette: tuple[float, float] | None = None,
    apply_accuracy: bool = False,
) -> list[tuple[float, float]]:
    """(card_metres, DPM) from 0 to max card range. DPM is 0 outside the fire gate."""
    ground = float(ammo.get("GroundRange") or 0)
    if ground <= 0:
        return []
    card_max = ground * CARD_RANGE_MULTIPLIER
    points: list[tuple[float, float]] = []
    card = 0.0
    while card <= card_max + 1e-9:
        world = card / CARD_RANGE_MULTIPLIER
        points.append(
            (
                card,
                dpm_at_world(
                    weapon,
                    ammo,
                    armor,
                    world,
                    face,
                    gun_count,
                    damage_type,
                    silhouette,
                    apply_accuracy,
                ),
            )
        )
        card += range_step_card
    last_card = points[-1][0] if points else -1.0
    if abs(last_card - card_max) > range_step_card * 0.1:
        world = ground
        points.append(
            (
                card_max,
                dpm_at_world(
                    weapon,
                    ammo,
                    armor,
                    world,
                    face,
                    gun_count,
                    damage_type,
                    silhouette,
                    apply_accuracy,
                ),
            )
        )
    return points


def sum_series(series_list: Iterable[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    merged: dict[float, float] = {}
    for series in series_list:
        for card, dpm in series:
            merged[card] = merged.get(card, 0.0) + dpm
    return sorted(merged.items())


def time_to_kill_s(hit_points: float, dpm: float) -> float | None:
    if dpm <= 0 or hit_points <= 0:
        return None
    return float(hit_points) / (dpm / 60.0)


def interpolate_dpm(series: list[tuple[float, float]], card_m: float) -> float:
    if not series:
        return 0.0
    if card_m <= series[0][0]:
        return series[0][1]
    if card_m >= series[-1][0]:
        return series[-1][1]
    for i in range(1, len(series)):
        left_r, left_d = series[i - 1]
        right_r, right_d = series[i]
        if left_r <= card_m <= right_r:
            if right_r == left_r:
                return left_d
            t = (card_m - left_r) / (right_r - left_r)
            return left_d + t * (right_d - left_d)
    return series[-1][1]
