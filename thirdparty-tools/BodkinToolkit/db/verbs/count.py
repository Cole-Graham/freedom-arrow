"""db count — print row count for a table."""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "count", "row count")
    sp.add_argument("table")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    out.emit(str(len(storage.load_rows(args.table))))
