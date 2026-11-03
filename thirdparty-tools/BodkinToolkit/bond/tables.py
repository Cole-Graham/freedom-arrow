"""Tiny db-backed table cache for bond.

Loads tables on demand via `db dump` (typed rows), lets bond mutate them in
memory, and flushes dirtied tables back via `db load` (one atomic write per
table). Keeps bond's storage access entirely behind db.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List

import yaml
try:
    from yaml import CSafeLoader as _Loader, CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader, SafeDumper as _Dumper

from ..core import proc


class Tables:
    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._dirty: set = set()

    def get(self, table: str) -> List[Dict[str, Any]]:
        if table not in self._cache:
            r = proc.run_tool("db", "dump", table, capture=True)
            self._cache[table] = (yaml.load(r.stdout, Loader=_Loader) if r.stdout else []) or []
        return self._cache[table]

    def mark(self, table: str) -> None:
        self._dirty.add(table)

    def next_id(self, table: str) -> int:
        ids = [r["id"] for r in self.get(table) if isinstance(r.get("id"), int)]
        return (max(ids) + 1) if ids else 1

    def flush(self) -> None:
        for table in self._dirty:
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
