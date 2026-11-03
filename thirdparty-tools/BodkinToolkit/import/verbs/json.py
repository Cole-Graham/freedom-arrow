"""import json — translate every game JSON table in a directory into db."""
from __future__ import annotations

from pathlib import Path

from ...core import args as core_args, out, prompt, proc
from .. import translate
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "json", "import every JSON table from a directory")
    sp.add_argument("--from", dest="src", metavar="DIR",
                    help="source directory (default: repo json/)")
    sp.add_argument("--yes", action="store_true",
                    help="do not prompt even if db already has rows")


def run(args):
    src = Path(getattr(args, "src", None) or _shared.default_json_dir())
    if not src.is_dir():
        out.error(f"ERR cannot find json directory {src}")

    # prompt once if any target table is already populated
    if not getattr(args, "yes", False):
        populated = []
        for table in translate.FILE_TABLE.values():
            r = proc.run_tool("db", "count", table, check=False, capture=True)
            if r.returncode == 0 and (r.stdout or "0").strip().isdigit() \
                    and int(r.stdout.strip()) > 0:
                populated.append(table)
        if populated:
            try:
                prompt.confirm_destructive(
                    f"db already has rows in {len(populated)} table(s); "
                    f"import will replace them. Proceed?", yes_flag=False)
            except prompt.Cancelled as e:
                out.error(f"ERR {e}")

    total = 0
    for filename, table in translate.FILE_TABLE.items():
        path = src / filename
        if not path.exists():
            out.emit(f"WARN skipping {filename}: not found")
            continue
        n = _shared.load_into_db(table, path)
        total += n
        out.emit(f"  {filename:<28} -> {table:<20} {n:>6} rows")
    out.emit(f"Done. {total} row(s) imported into db.")


