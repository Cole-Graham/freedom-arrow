"""db next-id — print max(id)+1, or 1 for an empty table."""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "next-id", "max(id)+1")
    sp.add_argument("table")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    out.emit(str(compute(schema, args.table)))


def compute(schema, table) -> int:
    pk = schema.primary_key(table)
    rows = storage.load_rows(table)
    ids = [r.get(pk) for r in rows if isinstance(r.get(pk), int)]
    return (max(ids) + 1) if ids else 1
