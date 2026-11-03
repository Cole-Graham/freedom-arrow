"""link touch — recompute + persist link_info for (table id) pairs."""
from __future__ import annotations

from collections import defaultdict

from ...core import args as core_args, out
from .. import graph as G
from ..writer import write_link_info


def configure(parser):
    sp = core_args.add_verb(parser, "touch", "recompute + persist link_info for pairs")
    sp.add_argument("pairs", nargs="+", metavar="TABLE ID ...",
                    help="alternating table id table id ...")


def run(args):
    toks = args.pairs
    if len(toks) % 2 != 0:
        out.error("ERR touch needs an even number of args: table id [table id ...]")
    pairs = []
    seen = set()
    for i in range(0, len(toks), 2):
        table = toks[i]
        try:
            eid = int(toks[i + 1])
        except ValueError:
            out.error(f"ERR '{toks[i + 1]}' is not an integer id")
        if (table, eid) not in seen:
            seen.add((table, eid))
            pairs.append((table, eid))

    g = G.Graph(G.load_tables())
    by_table = defaultdict(dict)
    ok, failed = [], []
    for table, eid in pairs:
        if table in G.BRIDGE_SET or table not in G.CANONICAL:
            out.emit(f"  WARN {table} {eid}: not a canonical table; skipped")
            failed.append((table, eid))
            continue
        if not g.exists(table, eid):
            out.emit(f"  WARN {table} {eid}: not found; skipped")
            failed.append((table, eid))
            continue
        by_table[table][eid] = g.compute(table, eid)
        ok.append((table, eid))

    for table, blocks in by_table.items():
        write_link_info(table, blocks)
        out.emit(f"  touched {table}: {len(blocks)} row(s)")

    out.emit(f"Done. {len(ok)} touched, {len(failed)} failed.")
    return 1 if failed else 0
