"""Load decrypted vanilla JSON and optional constants overlays."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import FIELD_TO_FILE, FILE_TO_FIELD, NEEDED_FIELDS


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
            if not isinstance(fields, dict):
                continue
            if row_id in dest:
                dest[row_id].update(fields)
                dest[row_id]["Id"] = row_id
            else:
                row = dict(fields)
                row["Id"] = row_id
                dest[row_id] = row
    return merged


def load_dataset(vanilla_dir: Path, overlay_dir: Path | None = None) -> dict[str, dict[int, dict[str, Any]]]:
    tables = load_vanilla(vanilla_dir)
    if overlay_dir:
        tables = apply_overlay(tables, overlay_dir)
    return tables
