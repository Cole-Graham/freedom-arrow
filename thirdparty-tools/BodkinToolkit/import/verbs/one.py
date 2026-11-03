"""import one — translate a single table from one JSON file into db."""
from __future__ import annotations

from pathlib import Path

from ...core import args as core_args, out
from .. import translate
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "one", "import a single table from one JSON file")
    sp.add_argument("table")
    sp.add_argument("--from", dest="src", metavar="FILE",
                    help="source JSON file (default: repo json/<MappedName>)")
    sp.add_argument("--yes", action="store_true", help="(accepted; unused here)")


def run(args):
    table = args.table
    if table not in translate.TABLE_FILE:
        out.error(f"ERR '{table}' is not an importable table; one of "
                  f"{', '.join(sorted(translate.TABLE_FILE))}")
    if getattr(args, "src", None):
        path = Path(args.src)
    else:
        path = _shared.default_json_dir() / translate.TABLE_FILE[table]
    if not path.exists():
        out.error(f"ERR cannot find {path}")
    n = _shared.load_into_db(table, path)
    out.emit(f"Done. {n} row(s) imported into {table}.")
