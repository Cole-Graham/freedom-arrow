"""db get — read rows by id or --where field match."""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "get", "read one or more rows by id or field match")
    sp.add_argument("table")
    sp.add_argument("--id", type=int)
    sp.add_argument("--where", action="append", default=[], metavar="FIELD=VALUE")
    sp.add_argument("--fields", metavar="f1,f2,...")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    fields = helpers.project_fields(args.fields)
    rows = storage.load_rows(args.table)
    pk = schema.primary_key(args.table)

    if args.id is not None and args.where:
        out.error("ERR --id and --where are mutually exclusive")

    if args.id is not None:
        match = [r for r in rows if r.get(pk) == args.id]
        if not match:
            out.error(f"ERR table '{args.table}' has no row with id={args.id}")
        helpers.emit_records(schema, args.table, match[:1], fields)
        return

    if not args.where:
        out.error("ERR get requires --id or at least one --where")

    conds = []
    for w in args.where:
        if "=" not in w:
            out.error(f"ERR malformed --where '{w}'; expected field=value")
        f, _, v = w.partition("=")
        conds.append((f.strip(), helpers.parse_scalar(v)))

    selected = []
    for r in rows:
        ok = True
        for f, want in conds:
            got = schema.row_value(args.table, r, f)
            if got is helpers._MISSING:
                got = None
            if got != want:
                ok = False
                break
        if ok:
            selected.append(r)
    helpers.emit_records(schema, args.table, selected, fields)
