"""backup make — create a light (json/), heavy (bundle), or both snapshot."""
from __future__ import annotations

import shutil
from pathlib import Path

from ...core import args as core_args, out, paths, prompt
from ..bundle_path import resolve_bundle
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "make", "create a light | heavy | both snapshot")
    sp.add_argument("kind", choices=("light", "heavy", "both"))
    sp.add_argument("--name", help="human-readable prefix for the snapshot dir")
    sp.add_argument("--bundle", help="bundle path (heavy; default: resolved)")
    sp.add_argument("--yes", action="store_true", help="overwrite an existing snapshot dir")


def _dirname(name):
    ts = _shared.timestamp()
    return f"{name}_{ts}" if name else ts


def _make_light(dirname, yes):
    src = paths.JSON_DIR
    if not src.is_dir():
        out.error("ERR target absent; re-import or re-unpack first", exit_code=2)
    dest = paths.BACKUPS_DIR / "light" / dirname
    if dest.exists() and not yes:
        prompt.confirm_destructive(f"{dest} exists. Overwrite?", yes_flag=False)
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.glob("*.json")):
        shutil.copy2(f, dest / f.name)
        n += 1
    out.emit(f"  light: {n} json file(s) -> {dest}")


def _make_heavy(dirname, bundle, yes):
    b = resolve_bundle(bundle)
    if not b.exists():
        out.error(f"ERR cannot find bundle at {b}", exit_code=2)
    dest = paths.BACKUPS_DIR / "heavy" / dirname
    if dest.exists() and not yes:
        prompt.confirm_destructive(f"{dest} exists. Overwrite?", yes_flag=False)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(b, dest / b.name)
    out.emit(f"  heavy: {b.name} -> {dest}")


def run(args):
    dirname = _dirname(args.name)
    yes = getattr(args, "yes", False)
    if args.kind in ("light", "both"):
        _make_light(dirname, yes)
    if args.kind in ("heavy", "both"):
        _make_heavy(dirname, getattr(args, "bundle", None), yes)
    out.emit("Done.")
    return 0
