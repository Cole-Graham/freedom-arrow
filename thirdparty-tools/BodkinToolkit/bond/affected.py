"""Compute the affected canonical entity list after a bond mutation, for
the trailing `link touch`."""
from __future__ import annotations

from typing import List, Tuple


def affected_pairs(unit_id: int, old_w: int, new_w: int,
                   swapped_turret_ids, ammo_ids) -> List[Tuple[str, int]]:
    pairs: List[Tuple[str, int]] = [("units", unit_id),
                                    ("weapons", old_w), ("weapons", new_w)]
    for tid in swapped_turret_ids:
        pairs.append(("turrets", tid))
    for aid in ammo_ids:
        pairs.append(("ammunition", aid))
    # dedupe preserving order
    seen, out = set(), []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
