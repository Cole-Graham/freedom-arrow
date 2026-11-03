"""db put — upsert a row (create or update)."""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active
from . import next_id


def configure(parser):
    sp = helpers.add_verb(parser, "put", "upsert a row")
    sp.add_argument("table")
    sp.add_argument("--id", type=int)
    sp.add_argument("--set", action="append", default=[], dest="sets",
                    metavar="FIELD=VALUE")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    pk = schema.primary_key(args.table)

    if not args.sets:
        out.error("ERR put requires at least one --set")

    updates = _parse_and_validate(schema, args.table, args.sets)

    rows = storage.load_rows(args.table)
    idx = None
    if args.id is not None:
        for i, r in enumerate(rows):
            if r.get(pk) == args.id:
                idx = i
                break

    allocated = None
    if idx is not None:
        # update existing
        row = rows[idx]
        _apply(row, updates)
    else:
        # create
        new_id = args.id if args.id is not None else next_id.compute(schema, args.table)
        if args.id is None:
            allocated = new_id
        row = {pk: new_id}
        _apply(row, updates)
        _check_required(schema, args.table, row)
        rows.append(row)

    storage.save_rows(args.table, rows)
    if allocated is not None:
        out.emit(str(allocated))


def _parse_and_validate(schema, table, sets):
    updates = []
    for token in sets:
        try:
            key, value = helpers.parse_set(token)
        except ValueError as e:
            out.error(str(e))
        top = key.split(".")[0]
        if "." in key:
            attrs = schema.field_for_write(table, top)
            if attrs.get("type") != "map":
                out.error(f"ERR dot-path --set requires field '{top}' to be a map")
        else:
            schema.validate_write_value(table, top, value)
        updates.append((key, value))
    return updates


def _apply(row, updates):
    for key, value in updates:
        if "." in key:
            helpers.set_nested(row, key, value)
        else:
            row[key] = value


def _check_required(schema, table, row):
    tbl = schema.tables[table]
    for fname, attrs in tbl.items():
        if not isinstance(attrs, dict):
            continue
        if attrs.get("primary"):
            continue
        if attrs.get("required") and row.get(fname) is None:
            out.error(f"ERR field '{fname}' is required but was not provided")
