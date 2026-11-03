"""Shared export helpers: read db rows, load baseline JSON, build, write."""
from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any, Dict, List

import yaml
try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

from ...core import paths, proc
from .. import translate


def db_rows(table: str) -> List[Dict[str, Any]]:
    r = proc.run_tool("db", "dump", table, capture=True)
    data = yaml.load(r.stdout, Loader=_Loader) if r.stdout else []
    return data or []


def baseline_rows(table: str, baseline_dir: Path) -> List[Dict[str, Any]]:
    path = baseline_dir / translate.TABLE_FILE[table]
    if not path.exists():
        return []
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except _json.JSONDecodeError:
        return []


def build_table(table: str, baseline_dir: Path) -> List[Dict[str, Any]]:
    rows = db_rows(table)
    base = baseline_rows(table, baseline_dir)
    return translate.BUILDERS[table](rows, base)


def write_json(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def default_json_dir() -> Path:
    return paths.JSON_DIR
