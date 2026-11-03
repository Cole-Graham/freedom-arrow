"""link init — recompute + persist link_info for every canonical row.

Reuses the rows already loaded for the graph, so each table is serialized
exactly once on write (no redundant re-dump).
"""
from __future__ import annotations

from ...core import args as core_args, out
from .. import graph as G
from ..writer import bulk_write_rows


def configure(parser):
    core_args.add_verb(parser, "init", "recompute + persist link_info for every canonical row")


def run(args):
    data = G.load_tables()
    g = G.Graph(data)
    failed = 0
    for table in G.CANONICAL:
        rows = data[table]
        done = 0
        for row in rows:
            rid = row.get("id")
            if rid is None:
                failed += 1
                continue
            try:
                row["link_info"] = g.compute(table, rid)
                done += 1
            except Exception as e:  # noqa: BLE001
                out.emit(f"  WARN {table} {rid}: {e}")
                failed += 1
        bulk_write_rows(table, rows)
        out.emit(f"  processing {table}: {done}/{len(rows)} done")
    out.emit("Done. link_info computed for all canonical tables.")
    return 1 if failed else 0
