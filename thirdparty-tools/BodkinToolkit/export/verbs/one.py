"""export one — rebuild a single table to a file."""
from __future__ import annotations

from pathlib import Path

from ...core import args as core_args, out
from .. import translate
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "one", "rebuild a single table to a file")
    sp.add_argument("table")
    sp.add_argument("--out", metavar="FILE", required=True, help="output JSON file")
    sp.add_argument("--baseline", metavar="DIR",
                    help="baseline JSON dir (default: repo json/)")
    sp.add_argument("--yes", action="store_true", help="(accepted; unused)")


def run(args):
    table = args.table
    if table not in translate.BUILDERS:
        out.error(f"ERR unknown table '{table}'")
    baseline_dir = Path(args.baseline) if getattr(args, "baseline", None) \
        else _shared.default_json_dir()
    rows = _shared.build_table(table, baseline_dir)
    _shared.write_json(rows, Path(args.out))
    out.emit(f"Done. {len(rows)} row(s) -> {args.out}")
