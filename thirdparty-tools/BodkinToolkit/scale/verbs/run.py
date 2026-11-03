"""scale run — compute current + min_range from real_world for ammunition."""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml
try:
    from yaml import CSafeLoader as _Loader, CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader, SafeDumper as _Dumper

from ...core import args as core_args, out, proc
from .. import formula


def configure(parser):
    sp = core_args.add_verb(parser, "run", "scale ammo ranges from real_world")
    sp.add_argument("--only", nargs="*", type=int, metavar="ID",
                    help="process only these ammo ids")
    sp.add_argument("--dry-run", action="store_true", help="compute and report, no write")


def run(args):
    r = proc.run_tool("db", "dump", "ammunition", capture=True)
    rows = yaml.load(r.stdout, Loader=_Loader) if r.stdout else []
    only = set(args.only) if getattr(args, "only", None) else None

    stats = {"total": 0, "updated": 0, "missing": 0}
    for row in rows:
        if only is not None and row.get("id") not in only:
            continue
        formula.process(row, stats)

    if not args.dry_run and stats["updated"]:
        text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                         default_flow_style=False, width=4096)
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False,
                                         encoding="utf-8") as tf:
            tf.write(text)
            tmp = tf.name
        try:
            proc.run_tool("db", "load", "ammunition", "--from", tmp, capture=True)
        finally:
            Path(tmp).unlink(missing_ok=True)

    mode = "DRY-RUN " if args.dry_run else ""
    out.emit(f"{mode}scaled: total={stats['total']} updated={stats['updated']} "
             f"missing-real_world={stats['missing']}")
    return 0
