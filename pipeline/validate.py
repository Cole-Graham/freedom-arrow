"""Foreign keys across the 24 tables.

The check runs on the merged rows, before any ciphertext or zip is written.
Zero and missing values are unset links. A miss that was already in the
vanilla rows is left alone so a game quirk does not block an unrelated edit.
"""

from __future__ import annotations

from pipeline.errors import PipelineError

# (source file, field, target file). Names are the constants filenames.
LINKS: tuple[tuple[str, str, str], ...] = (
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
)


def validate_tables(merged: dict[str, list], vanilla: dict[str, list] | None = None) -> None:
    """Raise PipelineError listing every broken link."""
    ids = {name: _ids(rows) for name, rows in merged.items()}
    old_ids = {name: _ids(rows) for name, rows in vanilla.items()} if vanilla else {}
    problems: list[str] = []
    for source, field, target in LINKS:
        target_ids = ids.get(target, set())
        previous = old_ids.get(target, set())
        for row in merged.get(source) or []:
            if not isinstance(row, dict) or "Id" not in row or field not in row:
                continue
            value = row[field]
            if _unset(value):
                continue
            key = _id_key(value)
            if key is None or key in target_ids:
                continue
            if _preexisting(vanilla, previous, source, row, field, key):
                continue
            problems.append(f"{source} Id {row['Id']} field {field} missing {target} {value}")
    if problems:
        raise PipelineError("broken links:\n" + "\n".join(problems))


def _preexisting(
    vanilla: dict[str, list] | None,
    previous_ids: set[str],
    source: str,
    row: dict,
    field: str,
    key: str,
) -> bool:
    if vanilla is None or key in previous_ids:
        return False
    for old in vanilla.get(source) or []:
        if isinstance(old, dict) and old.get("Id") == row.get("Id"):
            return old.get(field) == row.get(field)
    return False


def _ids(rows) -> set[str]:
    found: set[str] = set()
    if not isinstance(rows, list):
        return found
    for row in rows:
        if isinstance(row, dict) and "Id" in row:
            key = _id_key(row["Id"])
            if key is not None:
                found.add(key)
    return found


def _id_key(value) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _unset(value) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False
