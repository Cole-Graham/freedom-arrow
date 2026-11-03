"""link walk — enriched view of an entity and its relations.

UP pass climbs to enclosing entities (depth-limited), then an optional single
DOWN pass enriches siblings (weapons/ammo of collected units). Relations are
recomputed from the graph, not read from stored link_info.
"""
from __future__ import annotations

from ...core import args as core_args, out
from .. import graph as G

_CORE = {"units", "weapons", "ammunition"}


def configure(parser):
    sp = core_args.add_verb(parser, "walk", "render an enriched view of an entity")
    sp.add_argument("table")
    sp.add_argument("id", type=int)
    sp.add_argument("--depth", type=int, default=1, help="how far to climb UP (default 1)")
    sp.add_argument("--down-once", action="store_true",
                    help="after the UP walk, do one DOWN pass to add siblings")
    sp.add_argument("--fields-on", action="append", default=[], metavar="TABLE=f1,f2",
                    help="project specific fields when rendering rows of TABLE")


def _fields_map(specs):
    out_map = {}
    for spec in specs:
        if "=" in spec:
            t, fs = spec.split("=", 1)
            out_map[t.strip()] = [f.strip() for f in fs.split(",") if f.strip()]
    return out_map


def _fmt(row, fields):
    if fields:
        bits = " ".join(f"{f}={row.get(f)}" for f in fields)
        return f"  #{row.get('id'):<5} {bits}"
    name = row.get("name") or row.get("ui_name") or "?"
    hud = row.get("hud_name")
    hud_s = f" [{hud}]" if hud and hud != name else ""
    tags = row.get("tags")
    tag_s = f"  tags={tags}" if tags else ""
    return f"  #{row.get('id'):<5} {name}{hud_s}{tag_s}"


def run(args):
    table = args.table
    if table not in G.CANONICAL:
        out.error(f"ERR '{table}' is not a canonical table")
    g = G.Graph(G.load_tables())
    if not g.exists(table, args.id):
        out.error(f"ERR {table} id={args.id} not found")
    fields = _fields_map(args.fields_on)

    units, weapons, ammo = set(), set(), set()
    if table == "units":
        units.add(args.id)
    elif table == "weapons":
        weapons.add(args.id)
    elif table == "ammunition":
        ammo.add(args.id)
    else:
        # non-core seed: just print its link block
        out.emit(f"=== link walk: seed={table} id={args.id} ===")
        block = g.compute(table, args.id)
        import yaml
        out.emit(yaml.safe_dump(block, sort_keys=False, allow_unicode=True,
                                default_flow_style=False, width=4096).rstrip("\n"))
        return 0

    # UP pass (depth controls how many climbing rounds)
    for _ in range(max(1, args.depth)):
        for aid in list(ammo):
            weapons.update(g.ammo_weapons.get(aid, ()))
            units.update(g.ammo_units.get(aid, ()))
        for wid in list(weapons):
            units.update(g.weapon_units.get(wid, ()))

    # DOWN pass (single, bounded)
    if args.down_once or table in _CORE:
        for uid in list(units):
            weapons.update(g.unit_weapons.get(uid, ()))
            weapons.update(g.unit_squad_weapons.get(uid, ()))
            ammo.update(g.unit_ammo.get(uid, ()))
        for wid in list(weapons):
            ammo.update(g.weapon_ammo.get(wid, ()))

    out.emit(f"=== link walk: seed={table} id={args.id} ===")
    for label, idx, ids in (
        ("units", g.units_idx, units),
        ("weapons", g.weapons_idx, weapons),
        ("ammunition", g.ammo_idx, ammo),
    ):
        out.emit(f"-- {label} ({len(ids)}) --")
        flds = fields.get(label)
        for i in sorted(ids):
            row = idx.get(i)
            out.emit(_fmt(row, flds) if row else f"  #{i:<5} <missing>")
    return 0
