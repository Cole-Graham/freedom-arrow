"""Load decrypted vanilla JSON and optional constants overlays."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .constants import FIELD_TO_FILE, FILE_TO_FIELD, NEEDED_FIELDS, VANILLA_COVER


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_vanilla_dir(root: Path | None = None) -> Path | None:
    cache = (root or repo_root()) / "cache" / "vanilla"
    if not cache.is_dir():
        return None
    dirs = [p for p in cache.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


PACKAGE_DIR = "UserData/FreedomArrow/"


def extract_package(package: Path, root: Path | None = None) -> tuple[Path, str]:
    """Copy the constants and game-config.json of a Freedom Arrow .bamod (gameplay or complete package)
    to cache/fa-package and return (constants dir, version). The package is the build the game loads;
    China and every later change are in it. The release folders cannot rebuild 0.8 and later constants."""
    out = (root or repo_root()) / "cache" / "fa-package"
    shutil.rmtree(out, ignore_errors=True)
    with zipfile.ZipFile(package) as bamod:
        names = [
            n for n in bamod.namelist()
            if re.fullmatch(re.escape(PACKAGE_DIR) + r"(constants/[^/]+\.json|game-config\.json)", n)
        ]
        if not any("/constants/" in n for n in names):
            raise FileNotFoundError(f"{package.name} has no {PACKAGE_DIR}constants. Pick a Freedom Arrow gameplay or complete package.")
        for name in names:
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bamod.read(name))
        version = json.loads(bamod.read("mod.json")).get("version") if "mod.json" in bamod.namelist() else None
    return out / PACKAGE_DIR / "constants", version or package.stem


def mod_cover(overlay_dir: Path) -> dict[str, float]:
    """Cover values of the mod: game-config.json next to its constants folder."""
    config = _read_json(overlay_dir.parent / "game-config.json")
    return {
        "forest_taken": float(config.get("ForestDamageTaken", VANILLA_COVER["forest_taken"])),
        "building_floor": float(config.get("BuildingDamageFloor", VANILLA_COVER["building_floor"])),
        "building_per_soldier": float(config.get("BuildingDamagePerSoldier", VANILLA_COVER["building_per_soldier"])),
    }


def _index_rows(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed: dict[int, dict[str, Any]] = {}
    for row in rows:
        indexed[int(row["Id"])] = dict(row)
    return indexed


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_vanilla(vanilla_dir: Path) -> dict[str, dict[int, dict[str, Any]]]:
    tables: dict[str, dict[int, dict[str, Any]]] = {}
    for field in NEEDED_FIELDS:
        filename = FIELD_TO_FILE[field]
        # Vanilla snapshot uses the MonoBehaviour field name as the file stem.
        path = vanilla_dir / f"{field}.json"
        if not path.is_file():
            path = vanilla_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing table {field} in {vanilla_dir}")
        payload = _read_json(path)
        if not isinstance(payload, list):
            raise ValueError(f"{path} is not a JSON array")
        tables[field] = _index_rows(payload)
    return tables


def apply_overlay(
    tables: dict[str, dict[int, dict[str, Any]]],
    overlay_dir: Path,
) -> dict[str, dict[int, dict[str, Any]]]:
    """Merge `{ "Id": { "Field": value } }` patches onto a copy of vanilla."""
    merged = {name: {row_id: dict(row) for row_id, row in rows.items()} for name, rows in tables.items()}
    if not overlay_dir.is_dir():
        raise FileNotFoundError(overlay_dir)
    partial: list[str] = []
    for path in sorted(overlay_dir.glob("*.json")):
        field = FILE_TO_FIELD.get(path.name)
        if field is None or field not in merged:
            continue
        patch = _read_json(path)
        if not isinstance(patch, dict) or not patch:
            continue
        dest = merged[field]
        for key, fields in patch.items():
            row_id = int(key)
            if fields is None:  # a null row deletes it (retired options, removed squad members)
                dest.pop(row_id, None)
                continue
            if not isinstance(fields, dict):
                continue
            if row_id in dest:
                dest[row_id].update(fields)
                dest[row_id]["Id"] = row_id
            else:
                row = dict(fields)
                row["Id"] = row_id
                if tables[field] and not set(next(iter(tables[field].values()))) <= set(row):
                    partial.append(f"{field} {row_id}")
                dest[row_id] = row
    if partial:
        raise ValueError(
            f"The mod changes {len(partial)} rows that are not in this vanilla snapshot (for example {', '.join(partial[:3])}). "
            "The snapshot is older than the game the build was made for. Run python -m pipeline decrypt again."
        )
    return merged


def load_dataset(vanilla_dir: Path, overlay_dir: Path | None = None) -> dict[str, dict[int, dict[str, Any]]]:
    tables = load_vanilla(vanilla_dir)
    if overlay_dir:
        tables = apply_overlay(tables, overlay_dir)
    return tables
