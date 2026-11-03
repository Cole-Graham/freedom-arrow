"""Persist computed link_info back into db via the bulk `db load` primitive.

Writing a whole map field through `db put --set` is not expressible, so link
reads a table's rows (db dump), sets `link_info` on the targeted ids, and
loads the whole table back (one atomic, O(N) write per table).
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


def write_link_info(table: str, blocks: Dict[int, Dict[str, Any]]) -> None:
    """Set link_info on the given ids (block may be empty -> store {})."""
    r = proc.run_tool("db", "dump", table, capture=True)
    rows: List[Dict[str, Any]] = yaml.load(r.stdout, Loader=_Loader) if r.stdout else []
    rows = rows or []
    for row in rows:
        if row.get("id") in blocks:
            row["link_info"] = blocks[row["id"]]
    text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=4096)
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(text)
        tmp = tf.name
    try:
        proc.run_tool("db", "load", table, "--from", tmp, capture=True)
    finally:
        Path(tmp).unlink(missing_ok=True)


def bulk_write_rows(table, rows):
    """Write a full set of rows (already carrying link_info) to db in one
    load. Used by `init`, which already holds every row in memory."""
    import tempfile as _tf
    from pathlib import Path as _P
    text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=4096)
    with _tf.NamedTemporaryFile("w", suffix=".yml", delete=False, encoding="utf-8") as tf:
        tf.write(text)
        tmp = tf.name
    try:
        proc.run_tool("db", "load", table, "--from", tmp, capture=True)
    finally:
        _P(tmp).unlink(missing_ok=True)
