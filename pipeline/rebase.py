"""Three-way merge of an old vanilla snapshot, a new one, and mod/constants."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.constants import Overrides, kind, load_constants
from pipeline.errors import PipelineError, RebaseConflictError
from pipeline.snapshot import load_table, table_filename, write_manifest
from pipeline.tables import FIELD_ORDER


@dataclass(frozen=True)
class Conflict:
    table: str
    field: str
    row_id: str
    column: str
    reason: str
    old_vanilla: object
    new_vanilla: object
    constant: object

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "field": self.field,
            "id": self.row_id,
            "column": self.column,
            "reason": self.reason,
            "old_vanilla": self.old_vanilla,
            "new_vanilla": self.new_vanilla,
            "constant": self.constant,
        }


def collect_conflicts(old_dir: Path, new_dir: Path, overrides: Overrides) -> list[Conflict]:
    conflicts: list[Conflict] = []
    for field in FIELD_ORDER:
        table_overrides = overrides.get(field) or {}
        if not table_overrides:
            continue
        filename = table_filename(field)
        old_rows = _index(load_table(old_dir, field), filename)
        new_rows = _index(load_table(new_dir, field), filename)
        for row_id, fields in table_overrides.items():
            old_row = old_rows.get(row_id)
            new_row = new_rows.get(row_id)
            if new_row is None:
                if old_row is None:
                    raise PipelineError(f"{filename} has no Id {row_id}")
                conflicts.append(
                    Conflict(filename, field, row_id, "", "row_deleted", _present(old_row), None, fields)
                )
                continue
            for column, value in fields.items():
                if column not in new_row:
                    if old_row is None or column not in old_row:
                        raise PipelineError(f"{filename} Id {row_id} has no field {column}")
                    conflicts.append(
                        Conflict(
                            filename,
                            field,
                            row_id,
                            column,
                            "field_removed",
                            old_row.get(column),
                            None,
                            value,
                        )
                    )
                    continue
                if kind(new_row[column]) != kind(value):
                    conflicts.append(
                        Conflict(
                            filename,
                            field,
                            row_id,
                            column,
                            "type_changed",
                            (old_row or {}).get(column),
                            new_row[column],
                            value,
                        )
                    )
                    continue
                vanilla_changed = old_row is not None and old_row.get(column) != new_row.get(column)
                if vanilla_changed:
                    conflicts.append(
                        Conflict(
                            filename,
                            field,
                            row_id,
                            column,
                            "both_changed",
                            old_row.get(column),
                            new_row[column],
                            value,
                        )
                    )
    return conflicts


def rebase(
    old_dir: Path,
    new_dir: Path,
    constants_dir: Path,
    manifest_path: Path,
    new_build_id: str,
    report_path: Path,
    accept: bool,
) -> list[Conflict]:
    """Compare snapshots. Write the manifest only when there is nothing left to review."""
    if not old_dir.is_dir():
        raise PipelineError(f"missing previous vanilla snapshot {old_dir}")
    if not new_dir.is_dir():
        raise PipelineError(f"missing new vanilla snapshot {new_dir}. Run decrypt first.")

    conflicts = collect_conflicts(old_dir, new_dir, load_constants(constants_dir))
    if conflicts:
        _write_report(report_path, old_dir.name, new_build_id, conflicts)
        if not accept:
            raise RebaseConflictError(report_path, conflicts)
        print(f"accepted {len(conflicts)} conflict(s); constants kept", flush=True)
    elif report_path.is_file():
        report_path.unlink()

    write_manifest(manifest_path, new_build_id)
    print(f"manifest -> {new_build_id}", flush=True)
    return conflicts


def _index(rows, table_name: str) -> dict[str, dict]:
    if not isinstance(rows, list):
        raise PipelineError(f"{table_name} is not a list of rows")
    indexed: dict[str, dict] = {}
    for row in rows:
        if isinstance(row, dict) and "Id" in row:
            indexed[str(row["Id"])] = row
    return indexed


def _present(row):
    if row is None:
        return None
    row_id = row.get("Id")
    return {"Id": row_id}


def _write_report(path: Path, old_build_id: str, new_build_id: str, conflicts: list[Conflict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "old_build_id": old_build_id,
        "new_build_id": new_build_id,
        "conflicts": [conflict.as_dict() for conflict in conflicts],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(conflicts)} conflict(s))", flush=True)
