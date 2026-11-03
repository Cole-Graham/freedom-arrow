"""db find — substring (default) or --exact search across one or more fields.

Usage: db find <table> <field-A> [<field-B> ...] <needle> [--sep C] [--exact]

All positionals after <table> are collected; the last is the needle, the
rest are the fields whose values are concatenated with --sep before matching.
"""
from __future__ import annotations

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "find", "substring/exact search across fields")
    sp.add_argument("table")
    sp.add_argument("terms", nargs="+", metavar="FIELD ... NEEDLE")
    sp.add_argument("--sep", default=";")
    sp.add_argument("--exact", action="store_true")
    sp.add_argument("--ci", action="store_true", help="case-insensitive match")


def run(args):
    schema = load_active()
    schema.require_table(args.table)

    if len(args.terms) < 2:
        out.error("ERR find requires at least one field and a needle")
    fields = args.terms[:-1]
    needle = args.terms[-1]

    rows = storage.load_rows(args.table)
    matched = []
    for r in rows:
        parts = []
        for f in fields:
            v = schema.row_value(args.table, r, f)
            if v is helpers._MISSING or v is None:
                parts.append("")
            else:
                parts.append(_scalar_str(v))
        joined = args.sep.join(parts)
        hay, nee = (joined.lower(), needle.lower()) if getattr(args, "ci", False) else (joined, needle)
        if (hay == nee) if args.exact else (nee in hay):
            matched.append(r)
    helpers.emit_records(schema, args.table, matched, None)


def _scalar_str(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)
