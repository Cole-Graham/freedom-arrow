"""db load — bulk-replace a table from a YAML list (stdin or --from).

The inbound bulk primitive. Used by `import` (json -> db) and by `link`
(recompute link_info across a whole table). Validates every field of every
row against the active schema, then writes the entire table in ONE atomic
save. This is O(N); repeated single-row `put`/`patch` is O(N^2) because each
call rewrites the whole file.

Input is a YAML list of complete row mappings, e.g.

    - {id: 1, name: BMP-3, type: 0}
    - {id: 2, name: T-90,  type: 0}

Read from --from PATH when given, otherwise from stdin. Prints the row
count written.
"""
from __future__ import annotations

import sys

import yaml
try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "load", "bulk-replace a table from YAML (stdin or --from)")
    sp.add_argument("table")
    sp.add_argument("--from", dest="src", metavar="PATH",
                    help="YAML file to read rows from (default: stdin)")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    pk = schema.primary_key(args.table)

    src = getattr(args, "src", None)
    text = open(src, encoding="utf-8").read() if src else sys.stdin.read()
    rows = yaml.load(text, Loader=_Loader) or []
    if not isinstance(rows, list):
        out.error("ERR load expects a YAML list of row mappings")

    tbl = schema.tables[args.table]
    passthrough = schema.is_passthrough(args.table)
    clean = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            out.error(f"ERR load row {i} is not a mapping")
        if not passthrough:
            for field, value in row.items():
                schema.validate_write_value(args.table, field, value)
            for fname, attrs in tbl.items():
                if not isinstance(attrs, dict) or attrs.get("primary"):
                    continue
                if attrs.get("required") and row.get(fname) is None:
                    out.error(f"ERR load row id={row.get(pk)}: field '{fname}' is required")
        clean.append(row)

    storage.save_rows(args.table, clean)
    out.emit(str(len(clean)))
