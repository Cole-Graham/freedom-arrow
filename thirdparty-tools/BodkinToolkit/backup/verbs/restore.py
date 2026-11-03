"""backup restore — restore json/ (light) or the bundle (heavy) from a snapshot."""
from __future__ import annotations

import shutil
from pathlib import Path

from ...core import args as core_args, out, paths, prompt
from ..bundle_path import resolve_bundle
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "restore", "restore from a snapshot (destructive)")
    sp.add_argument("--kind", choices=("light", "heavy"))
    sp.add_argument("--name", help="substring filter on snapshot dir names")
    sp.add_argument("--bundle", help="bundle path to restore into (heavy)")
    sp.add_argument("--yes", action="store_true", help="skip destructive confirmation")


def _pick(snaps):
    return prompt.select_one(
        "Choose a backup to restore:", snaps,
        label_fn=lambda s: f"{s.kind} {s.name}  ({_shared.human_size(s.size)})")


def run(args):
    snaps = _shared.list_snaps(getattr(args, "kind", None))
    if not snaps:
        out.error("ERR no backups found under backups/", exit_code=2)
    if getattr(args, "name", None):
        snaps = [s for s in snaps if args.name in s.name]
        if not snaps:
            out.error(f"ERR no backup matches '{args.name}'", exit_code=2)
    if len(snaps) == 1:
        chosen = snaps[0]
    else:
        chosen = _pick(snaps)

    yes = getattr(args, "yes", False)
    if chosen.kind == "light":
        target = paths.JSON_DIR
        if not target.exists():
            out.error("ERR target absent; re-import or re-unpack first", exit_code=2)
        prompt.confirm_destructive(
            f"Overwrite json/ from light snapshot '{chosen.name}'?", yes_flag=yes)
        n = 0
        for f in sorted(chosen.path.glob("*.json")):
            shutil.copy2(f, target / f.name)
            n += 1
        out.emit(f"restored {n} json file(s) from {chosen.name}")
    else:
        files = [f for f in chosen.path.iterdir() if f.is_file()]
        if not files:
            out.error("ERR heavy snapshot is empty", exit_code=2)
        target = resolve_bundle(getattr(args, "bundle", None))
        prompt.confirm_destructive(
            f"Overwrite bundle {target} from heavy snapshot '{chosen.name}'?",
            yes_flag=yes)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(files[0], target)
        out.emit(f"restored bundle {target.name} from {chosen.name}")
    return 0
