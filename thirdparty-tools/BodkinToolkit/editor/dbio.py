"""db-backed table cache for the editor.

Loads tables on demand via `db dump`, lets flows mutate rows in memory, and
flushes dirtied tables via `db load` (one atomic write each). All storage
access stays behind db. pk is 'id' for the core snake tables and 'Id' for the
passthrough reference tables (auto-detected).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
try:
    from yaml import CSafeLoader as _Loader, CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader, SafeDumper as _Dumper

from ..core import proc

PASSTHROUGH = {
    "countries", "specializations", "specialization_availabilities",
    "transport_availabilities", "armors", "unit_armors", "mobility",
    "unit_propulsions", "fly_presets", "sensors", "sensor_units",
    "abilities", "unit_abilities",
}


def pk_of(table: str) -> str:
    return "Id" if table in PASSTHROUGH else "id"


class Tables:
    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._dirty: set = set()

    def get(self, table: str) -> List[Dict[str, Any]]:
        if table not in self._cache:
            r = proc.run_tool("db", "dump", table, capture=True)
            self._cache[table] = (yaml.load(r.stdout, Loader=_Loader) if r.stdout else []) or []
        return self._cache[table]

    def by_id(self, table: str, _id: Any) -> Optional[Dict[str, Any]]:
        pk = pk_of(table)
        for r in self.get(table):
            if r.get(pk) == _id:
                return r
        return None

    def where(self, table: str, **eq) -> List[Dict[str, Any]]:
        return [r for r in self.get(table) if all(r.get(k) == v for k, v in eq.items())]

    def mark(self, table: str) -> None:
        self._dirty.add(table)

    def next_id(self, table: str) -> int:
        pk = pk_of(table)
        ids = [r.get(pk) for r in self.get(table) if isinstance(r.get(pk), int)]
        return (max(ids) + 1) if ids else 1

    def add(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        self.get(table).append(row)
        self.mark(table)
        return row

    def remove(self, table: str, predicate) -> int:
        rows = self.get(table)
        kept = [r for r in rows if not predicate(r)]
        n = len(rows) - len(kept)
        if n:
            self._cache[table] = kept
            self.mark(table)
        return n

    def dirty(self) -> bool:
        return bool(self._dirty)

    def flush(self) -> None:
        for table in sorted(self._dirty):
            text = yaml.dump(self._cache[table], Dumper=_Dumper, sort_keys=False,
                             allow_unicode=True, default_flow_style=False, width=4096)
            with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False,
                                             encoding="utf-8") as tf:
                tf.write(text)
                tmp = tf.name
            try:
                proc.run_tool("db", "load", table, "--from", tmp, capture=True)
            finally:
                Path(tmp).unlink(missing_ok=True)
        self._dirty.clear()
