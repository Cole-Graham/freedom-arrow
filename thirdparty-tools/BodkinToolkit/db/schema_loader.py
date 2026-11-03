"""Schema discovery, validation, and evolution helpers for `db`.

The active schema is the highest ``vN.yml`` under ``v3/db/schema/``. Each
file is a complete snapshot. Field evolution metadata is carried inline on
each field so reads against stale names/types raise loud, parseable errors:

    renamed_from / renamed_in   field is the new name of an old one
    deprecated_in               field is obsolete; reads must raise
    added_in / default          field added later; injected on read
    prior_type / converter      change-type bookkeeping
    manual_fix_required         change-type with no auto-conversion
    changed_in                  schema version a type change landed in

This module knows the schema shape only; it never touches storage files.
"""
from __future__ import annotations

import copy
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..core import io, paths

SCHEMA_DIR: Path = paths.tool_root("db") / "schema"

SUPPORTED_TYPES = ("int", "float", "str", "bool", "list", "map")

# Auto-conversions for change-type. (old, new) -> python callable.
_CASTS = {
    ("int", "float"): float,
    ("int", "str"): str,
    ("float", "str"): str,
    ("bool", "str"): str,
    ("int", "bool"): lambda v: bool(v),
}


class SchemaError(Exception):
    """User-facing error. The message already starts with ``ERR ``."""


def _value_matches(declared: str, value: Any) -> bool:
    if declared == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared == "str":
        return isinstance(value, str)
    if declared == "bool":
        return isinstance(value, bool)
    if declared == "list":
        return isinstance(value, list)
    if declared == "map":
        return isinstance(value, dict)
    return True  # unknown declared type: accept


def _py_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "map"
    return type(value).__name__


class Schema:
    def __init__(self, version: str, raw: Dict[str, Any], path: Path):
        self.version = version
        self.raw = raw
        self.path = path
        self.tables: Dict[str, Dict[str, Any]] = raw.get("tables", {}) or {}

    # -- table / field lookup -------------------------------------------------

    def require_table(self, table: str) -> Dict[str, Any]:
        if table not in self.tables:
            raise SchemaError(
                f"ERR table '{table}' is not declared in schema {self.version}"
            )
        return self.tables[table]

    def is_passthrough(self, table: str) -> bool:
        tbl = self.tables.get(table) or {}
        return bool(tbl.get("__passthrough__"))

    def primary_key(self, table: str) -> str:
        tbl = self.require_table(table)
        for fname, attrs in tbl.items():
            if isinstance(attrs, dict) and attrs.get("primary"):
                return fname
        return "id"

    def field_order(self, table: str) -> List[str]:
        """Readable fields in declaration order (deprecated fields excluded)."""
        if self.is_passthrough(table):
            return []
        tbl = self.require_table(table)
        return [f for f, a in tbl.items()
                if f != "__passthrough__" and not (isinstance(a, dict) and a.get("deprecated_in"))]

    # -- write-time validation ------------------------------------------------

    def field_for_write(self, table: str, field: str) -> Dict[str, Any]:
        if self.is_passthrough(table):
            self.require_table(table)
            return {}
        tbl = self.require_table(table)
        attrs = tbl.get(field)
        if attrs is None:
            raise SchemaError(
                f"ERR field '{field}' is not declared in schema {self.version}; "
                f"use db schema add-field"
            )
        if attrs.get("deprecated_in"):
            raise SchemaError(
                f"ERR field '{field}' is obsolete after schema "
                f"{attrs['deprecated_in']}; upgrade tool"
            )
        return attrs

    def validate_write_value(self, table: str, field: str, value: Any) -> None:
        if self.is_passthrough(table):
            return
        attrs = self.field_for_write(table, field)
        if value is None:
            return  # null is always permitted
        declared = attrs.get("type", "str")
        if not _value_matches(declared, value):
            raise SchemaError(
                f"ERR field '{field}' expects {declared}, got {_py_type_name(value)}"
            )

    # -- read-time resolution -------------------------------------------------

    def resolve_read(self, table: str, field: str) -> Tuple[Dict[str, Any], str]:
        """Return ``(attrs, storage_key)`` for reading ``field``.

        ``storage_key`` is where the value physically lives in a row (the old
        name if the field was renamed and never rewritten). Raises on stale
        names so callers can surface a loud upgrade error.
        """
        tbl = self.require_table(table)
        attrs = tbl.get(field)
        if attrs is not None:
            if attrs.get("deprecated_in"):
                raise SchemaError(
                    f"ERR field '{field}' is obsolete after schema "
                    f"{attrs['deprecated_in']}; upgrade tool"
                )
            return attrs, field
        # not a current field: is it an old name that was renamed?
        for newname, a in tbl.items():
            if isinstance(a, dict) and a.get("renamed_from") == field:
                raise SchemaError(
                    f"ERR field '{field}' was renamed to '{newname}' in schema "
                    f"{a.get('renamed_in', self.version)}, upgrade tool"
                )
        raise SchemaError(
            f"ERR field '{field}' is not declared in schema {self.version}"
        )

    def read_value(self, attrs: Dict[str, Any], raw_value: Any) -> Any:
        """Apply change-type conversion / loud errors when reading a value."""
        if raw_value is None:
            return None
        declared = attrs.get("type", "str")
        if _value_matches(declared, raw_value):
            # normalise int->float when a cast converter is recorded
            if declared == "float" and isinstance(raw_value, int) and attrs.get("converter") == "cast":
                return float(raw_value)
            return raw_value
        if attrs.get("manual_fix_required"):
            raise SchemaError(
                f"ERR field type changed to '{declared}' in schema "
                f"{attrs.get('changed_in', self.version)}; no auto-conversion "
                f"from '{attrs.get('prior_type', '?')}', manual data fix required"
            )
        prior = attrs.get("prior_type")
        cast = _CASTS.get((prior, declared)) if prior else None
        if attrs.get("converter") == "cast" and cast:
            try:
                return cast(raw_value)
            except Exception:
                pass
        return raw_value

    def row_value(self, table: str, row: Dict[str, Any], field: str) -> Any:
        """Read one field from a row, honoring rename/add/change-type rules."""
        if self.is_passthrough(table):
            return row[field] if field in row else _MISSING
        attrs, _ = self.resolve_read(table, field)
        if field in row:
            return self.read_value(attrs, row[field])
        old = attrs.get("renamed_from")
        if old and old in row:
            return self.read_value(attrs, row[old])
        # field absent: added-later fields surface their default/null
        if "added_in" in attrs or "default" in attrs:
            return attrs.get("default", None)
        return _MISSING

    def has_value(self, table: str, row: Dict[str, Any], field: str) -> bool:
        return self.row_value(table, row, field) is not _MISSING


_MISSING = object()


# -- discovery / load ---------------------------------------------------------

def _versions() -> List[Path]:
    if not SCHEMA_DIR.exists():
        return []
    files = [p for p in SCHEMA_DIR.glob("v*.yml") if p.stem[1:].isdigit()]
    return sorted(files, key=lambda p: int(p.stem[1:]))


def load_file(path: Path) -> Schema:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Schema(raw.get("version", path.stem), raw, path)


def load_active() -> Schema:
    files = _versions()
    if not files:
        raise SchemaError(f"ERR no schema files found in {SCHEMA_DIR}")
    return load_file(files[-1])


def load_version(vN: str) -> Schema:
    p = SCHEMA_DIR / f"{vN}.yml"
    if not p.exists():
        raise SchemaError(f"ERR schema version {vN} not found in {SCHEMA_DIR}")
    return load_file(p)


def next_version() -> Tuple[str, int]:
    files = _versions()
    n = int(files[-1].stem[1:]) if files else 0
    return f"v{n + 1}", n + 1


def write_snapshot(tables: Dict[str, Any], note: str) -> Path:
    """Write the next vN+1.yml snapshot. Returns the new file path."""
    vstr, _ = next_version()
    snapshot = {
        "version": vstr,
        "note": note,
        "introduced": date.today().isoformat(),
        "tables": tables,
    }
    text = yaml.safe_dump(snapshot, sort_keys=False, allow_unicode=True, default_flow_style=False, width=4096)

    def _validator(tmp: Path) -> None:
        reparsed = yaml.safe_load(tmp.read_text(encoding="utf-8"))
        if not isinstance(reparsed, dict) or "tables" not in reparsed:
            raise IOError("schema snapshot failed to round-trip")

    out_path = SCHEMA_DIR / f"{vstr}.yml"
    return io.atomic_write_text(out_path, text, validator=_validator)


def clone_tables(schema: Schema) -> Dict[str, Any]:
    return copy.deepcopy(schema.tables)


def supported_cast(old: str, new: str) -> bool:
    return (old, new) in _CASTS or old == new
