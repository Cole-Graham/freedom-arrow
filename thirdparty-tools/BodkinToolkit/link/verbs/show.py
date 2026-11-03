"""link show — compute and print one entity's link_info as YAML."""
from __future__ import annotations

import yaml

from ...core import args as core_args, out
from .. import graph as G


def configure(parser):
    sp = core_args.add_verb(parser, "show", "compute and print one entity's link_info")
    sp.add_argument("table")
    sp.add_argument("id", type=int)


def run(args):
    if args.table in G.BRIDGE_SET:
        out.error(f"ERR table '{args.table}' is a bridge table and has no link_info")
    if args.table not in G.CANONICAL:
        out.error(f"ERR '{args.table}' is not a canonical table")
    g = G.Graph(G.load_tables())
    if not g.exists(args.table, args.id):
        out.error(f"ERR {args.table} id={args.id} not found")
    block = g.compute(args.table, args.id)
    out.emit(yaml.safe_dump(block, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=4096).rstrip("\n"))
