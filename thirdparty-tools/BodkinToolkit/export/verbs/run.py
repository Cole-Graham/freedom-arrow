"""export run — rebuild every table to --out <dir> or --in-place."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from ...core import args as core_args, out, paths, prompt
from .. import translate
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "run", "rebuild every table to a dir or in place")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--out", metavar="DIR", help="write rebuilt JSON to this directory")
    g.add_argument("--in-place", action="store_true",
                   help="write back into repo json/ (light backup taken first)")
    sp.add_argument("--baseline", metavar="DIR",
                    help="baseline JSON dir for unmodelled fields (default: repo json/)")
    sp.add_argument("--only", nargs="*", metavar="TABLE", help="restrict to these tables")
    sp.add_argument("--yes", action="store_true", help="skip overwrite prompts")


def run(args):
    baseline_dir = Path(args.baseline) if getattr(args, "baseline", None) \
        else _shared.default_json_dir()
    tables = args.only or list(translate.BUILDERS)
    bad = [t for t in tables if t not in translate.BUILDERS]
    if bad:
        out.error(f"ERR unknown tables: {', '.join(bad)}")

    if args.in_place:
        out_dir = _shared.default_json_dir()
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup = paths.BACKUPS_DIR / "light" / f"{ts}_export"
        backup.mkdir(parents=True, exist_ok=True)
        for t in tables:
            s = out_dir / translate.TABLE_FILE[t]
            if s.exists():
                shutil.copy2(s, backup / s.name)
        out.emit(f"  backup: {backup}")
    else:
        out_dir = Path(args.out)
        if out_dir.exists() and any(out_dir.iterdir()) and not getattr(args, "yes", False):
            try:
                prompt.confirm_destructive(f"--out {out_dir} is not empty. Overwrite?",
                                           yes_flag=False)
            except prompt.Cancelled as e:
                out.error(f"ERR {e}")
        out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for t in tables:
        rows = _shared.build_table(t, baseline_dir)
        path = out_dir / translate.TABLE_FILE[t]
        _shared.write_json(rows, path)
        total += len(rows)
        out.emit(f"  wrote {path.name:<28} ({len(rows)} rows)")
    out.emit(f"Done. {total} row(s) across {len(tables)} table(s) -> {out_dir}")
