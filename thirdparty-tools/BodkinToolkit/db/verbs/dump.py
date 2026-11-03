"""db dump — emit a whole table as a raw YAML list of row mappings.

The outbound bulk primitive, symmetric with `db load`. Where `db all` is the
human record-block view, `db dump` is the machine-readable, type-exact view
that `export` and `link` consume (O(N), no fragile line parsing).
"""
from __future__ import annotations

import yaml
try:
    from yaml import CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeDumper as _Dumper

from ...core import out
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "dump", "emit a table as a raw YAML list")
    sp.add_argument("table")


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    rows = storage.load_rows(args.table)
    text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                          default_flow_style=False, width=4096)
    out.emit(text.rstrip("\n"))
