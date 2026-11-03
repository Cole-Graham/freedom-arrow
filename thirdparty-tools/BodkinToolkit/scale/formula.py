"""Soft-cap range compression — ported verbatim from v2 scale_ranges.py.

real_world.{ground,low_alt,high_alt} (meters) -> current.* (compressed,
game-balanced) + min_range.* (~5% of compressed max). Class heuristics
(long-range / A2A / unguided / CQB) preserved as-is.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

BASELINE_1_1 = 1000
CAP_LONG_RANGE = 15000
CAP_MEDIUM_RANGE = 10000

MULT_HEAVY_PENALTY = 0.4
MULT_SLIGHT_PENALTY = 0.85
MULT_KINEMATIC_BONUS = 1.15
MULT_LOOK_DOWN_COLLISION = 0.46
MULT_MIN_RANGE = 0.05

DOMAINS = ("ground", "low_alt", "high_alt")


def round_to(val: float, nearest: int) -> int:
    return int(round(val / nearest) * nearest)


def compress_range(real_range: float, cap: float) -> float:
    if real_range <= BASELINE_1_1:
        return real_range
    available = cap - BASELINE_1_1
    excess = real_range - BASELINE_1_1
    curve = math.tanh(excess / (available * 1.5))
    return BASELINE_1_1 + (available * curve)


def get_class_info(entry: Dict[str, Any]):
    name = (entry.get("name") or "").lower()
    hud = (entry.get("hud_name") or "").lower()
    long_range_kw = [
        "s300", "patriot", "s-300", "ballistic", "cruise", "radar",
        "mortar", "howitzer", "nlos", "favorit", "48n6",
    ]
    is_long_range = any(k in name or k in hud for k in long_range_kw)
    is_a2a = "missile aa" in name or "air-to-air" in name
    is_unguided = any(k in name for k in ["rpg", "law", "rocket"])
    is_cqb = any(k in name for k in ["infantry", "carbine", "pistol", "rifle"])
    return is_long_range, is_a2a, is_unguided, is_cqb


def _real_value(rw: Optional[Dict[str, Any]], domain: str) -> Optional[float]:
    if not isinstance(rw, dict):
        return None
    v = rw.get(domain)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def process(entry: Dict[str, Any], stats: Dict[str, Any]) -> bool:
    """Scale one ammo entry in place. Returns True iff any value changed."""
    stats["total"] += 1
    rw = entry.get("real_world")
    if not isinstance(rw, dict):
        stats["missing"] += 1
        return False

    is_long_range, is_a2a, is_unguided, is_cqb = get_class_info(entry)
    cap = CAP_LONG_RANGE if is_long_range else CAP_MEDIUM_RANGE

    current = dict(entry.get("current") or {})
    min_range = dict(entry.get("min_range") or {})
    touched = False
    any_real = False

    for domain in DOMAINS:
        real = _real_value(rw, domain)
        if real is None:
            continue
        any_real = True
        if real <= 0.0:
            current[domain] = float(real)
            min_range[domain] = 0.0
            touched = True
            continue

        base = compress_range(real, cap)
        final = base
        if domain == "low_alt":
            if is_long_range and is_a2a:
                final *= MULT_LOOK_DOWN_COLLISION
            elif is_long_range or is_unguided:
                final *= MULT_HEAVY_PENALTY
            elif is_a2a:
                final *= MULT_KINEMATIC_BONUS
        elif domain == "high_alt":
            if not is_long_range:
                final *= MULT_SLIGHT_PENALTY

        current[domain] = float(round_to(final, 100))
        if is_cqb:
            min_range[domain] = 0.0
        else:
            min_range[domain] = float(round_to(base * MULT_MIN_RANGE, 10))
        touched = True

    if not any_real:
        stats["missing"] += 1
        return False
    if touched:
        entry["current"] = current
        entry["min_range"] = min_range
        stats["updated"] += 1
    return touched
