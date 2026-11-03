"""db all — dump every row in a table."""
from __future__ import annotations

from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "all", "dump every row in a table")
    sp.add_argument("table")
    sp.add_argument("--fields", metavar="f1,f2,...")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    fields = helpers.project_fields(args.fields)
    rows = storage.load_rows(args.table)
    helpers.emit_records(schema, args.table, rows, fields)
