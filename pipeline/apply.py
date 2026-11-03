"""Merge mod/constants onto a vanilla snapshot and rebuild the object."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.constants import Overrides, kind
from pipeline.crypto import aes_encrypt
from pipeline.database import DatabaseBlob, parse_database, rebuild
from pipeline.errors import PipelineError
from pipeline.snapshot import load_table
from pipeline.tables import FIELD_ORDER, FIELD_TO_FILE


def apply_overrides(rows, overrides: dict[str, dict], table_name: str):
    """Return (rows, dirty). `rows` is a new list when anything changes."""
    if not overrides:
        return rows, False
    if not isinstance(rows, list):
        raise PipelineError(f"{table_name} is not a list of rows")

    index: dict[str, int] = {}
    for position, row in enumerate(rows):
        if isinstance(row, dict) and "Id" in row:
            index[str(row["Id"])] = position

    changed = False
    rows = [dict(row) if isinstance(row, dict) else row for row in rows]
    for row_id, fields in overrides.items():
        if row_id not in index:
            raise PipelineError(f"{table_name} has no Id {row_id}")
        row = rows[index[row_id]]
        if not isinstance(row, dict):
            raise PipelineError(f"{table_name} Id {row_id} is not an object")
        for key, value in fields.items():
            if key == "Id":
                raise PipelineError(f"{table_name} Id {row_id} cannot change Id")
            if key not in row:
                raise PipelineError(f"{table_name} Id {row_id} has no field {key}")
            old_kind = kind(row[key])
            new_kind = kind(value)
            if old_kind != new_kind:
                raise PipelineError(
                    f"{table_name} Id {row_id} field {key} type change: {old_kind} -> {new_kind}"
                )
            if row[key] != value:
                row[key] = value
                changed = True
    return rows, changed


def dumps_table(value) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_object(vanilla: Path, overrides: Overrides) -> tuple[bytes, list[str]]:
    """Rebuild the MonoBehaviour. Untouched fields keep their original ciphertext."""
    raw_path = vanilla / "object.bin"
    if not raw_path.is_file():
        raise PipelineError(f"missing {raw_path}. Run decrypt first.")
    blob = parse_database(raw_path.read_bytes())
    fields = dict(blob.fields)
    dirty: list[str] = []

    for field in FIELD_ORDER:
        table_overrides = overrides.get(field) or {}
        if not table_overrides:
            continue
        rows, changed = apply_overrides(load_table(vanilla, field), table_overrides, FIELD_TO_FILE[field])
        if not changed:
            continue
        fields[field] = aes_encrypt(dumps_table(rows))
        dirty.append(field)

    return rebuild(blob, fields), dirty


def original_blob(vanilla: Path) -> DatabaseBlob:
    raw_path = vanilla / "object.bin"
    if not raw_path.is_file():
        raise PipelineError(f"missing {raw_path}. Run decrypt first.")
    return parse_database(raw_path.read_bytes())
