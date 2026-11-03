"""backup list — list available snapshots, most recent first."""
from __future__ import annotations

from ...core import args as core_args, out
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "list", "list available snapshots")
    sp.add_argument("--kind", choices=("light", "heavy"))


def run(args):
    snaps = _shared.list_snaps(getattr(args, "kind", None))
    if not snaps:
        out.emit("no backups found")
        return 0
    for s in snaps:
        out.emit(f"  {s.kind:<6} {s.name:<32}  {_shared.iso(s.mtime)}  "
                 f"({_shared.human_size(s.size)})")
    return 0
