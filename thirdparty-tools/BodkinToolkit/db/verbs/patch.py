"""db patch — update an existing row; fail if the id is missing."""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active
from . import put as _put


def configure(parser):
    sp = helpers.add_verb(parser, "patch", "update existing row (fail if missing)")
    sp.add_argument("table")
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--set", action="append", default=[], dest="sets",
                    metavar="FIELD=VALUE")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    pk = schema.primary_key(args.table)

    if not args.sets:
        out.error("ERR patch requires at least one --set")

    updates = _put._parse_and_validate(schema, args.table, args.sets)

    rows = storage.load_rows(args.table)
    for r in rows:
        if r.get(pk) == args.id:
            _put._apply(r, updates)
            storage.save_rows(args.table, rows)
            return
    out.error(f"ERR table '{args.table}' has no row with id={args.id}")
