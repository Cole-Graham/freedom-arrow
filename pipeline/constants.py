"""Load mod/constants into id-keyed field overrides."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.errors import PipelineError
from pipeline.tables import FIELD_ORDER, FILE_TO_FIELD

# field name -> {row id -> {column -> value}}
Overrides = dict[str, dict[str, dict]]


def load_constants(directory: Path) -> Overrides:
    overrides: Overrides = {field: {} for field in FIELD_ORDER}
    if not directory.exists():
        return overrides
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() != ".json":
            raise PipelineError(f"unexpected file in {directory.name}: {path.name}")
        field = FILE_TO_FIELD.get(path.name)
        if field is None:
            raise PipelineError(f"unknown constants file {path.name}")
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PipelineError(f"{path.name} is not valid JSON: {exc}") from exc
        overrides[field] = _normalize(path.name, loaded)
    return overrides


def _normalize(filename: str, loaded) -> dict[str, dict]:
    if isinstance(loaded, dict):
        rows: dict[str, dict] = {}
        for key, value in loaded.items():
            if not isinstance(value, dict):
                raise PipelineError(f"{filename} entry {key} must be an object of fields")
            if "Id" in value:
                raise PipelineError(f"{filename} entry {key} must not repeat Id inside the fields")
            rows[str(key)] = dict(value)
        return rows
    if isinstance(loaded, list):
        rows = {}
        for index, item in enumerate(loaded):
            if not isinstance(item, dict) or "Id" not in item:
                raise PipelineError(f"{filename} item {index} needs an Id")
            fields = dict(item)
            row_id = fields.pop("Id")
            rows[str(row_id)] = fields
        return rows
    raise PipelineError(f"{filename} must be an object keyed by Id, or a list of rows")


def kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__
