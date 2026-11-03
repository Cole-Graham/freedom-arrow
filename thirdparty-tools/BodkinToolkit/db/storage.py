"""YAML storage backend for `db`.

One file per logical table at ``v3/world/yaml/<table>.yml``. Each file
is a YAML list of mappings. All writes go through
``core.io.atomic_write_text`` with a row-count round-trip validator so a
truncated/interrupted write can never replace the live file.

This module owns the table-name -> file-name mapping (implicit: identity).
It knows nothing about the schema; callers validate.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml
try:
    from yaml import CSafeLoader as _Loader, CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader, SafeDumper as _Dumper

from ..core import io, paths

YAML_DIR: Path = paths.YAML_DIR


def table_path(table: str) -> Path:
    """Logical table name -> storage file. Identity mapping, no overrides."""
    return YAML_DIR / f"{table}.yml"


def load_rows(table: str) -> List[Dict[str, Any]]:
    """Return the table's rows, or [] if the file is absent/empty."""
    text = io.read_text_safe(table_path(table))
    if text is None:
        return []
    data = yaml.load(text, Loader=_Loader)
    if data is None:
        return []
    if not isinstance(data, list):
        raise IOError(f"storage file for table {table!r} is not a YAML list")
    return data


def _dump(rows: List[Dict[str, Any]]) -> str:
    return yaml.dump(
        rows,
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=4096,
    )


def save_rows(table: str, rows: List[Dict[str, Any]]) -> Path:
    """Atomic write of the full table. Validator re-parses the tmp file and
    confirms the row count matches what we intended to write."""
    n = len(rows)

    def _validator(tmp: Path) -> None:
        reread = yaml.load(tmp.read_text(encoding="utf-8"), Loader=_Loader)
        reread = reread or []
        got = len(reread) if isinstance(reread, list) else -1
        if got != n:
            raise IOError(
                f"row count mismatch writing table {table!r}: "
                f"wrote {n}, re-read {got} (likely truncated write)"
            )

    return io.atomic_write_text(table_path(table), _dump(rows), validator=_validator)


def format_value(value: Any) -> str:
    """Render a single field value on ONE line.

    Scalars print bare (``name: BMP-3``). Lists/maps print as inline-flow
    YAML so callers can parse the output line by line.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    # list / dict -> inline flow YAML, single line
    dumped = yaml.safe_dump(
        value,
        default_flow_style=True,
        allow_unicode=True,
        width=10 ** 9,
        sort_keys=False,
    ).strip()
    return dumped
