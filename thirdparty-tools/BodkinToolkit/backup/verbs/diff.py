"""backup diff — diff a named snapshot against the live json/."""
from __future__ import annotations

from ...core import args as core_args, out, paths, proc
from . import _shared


def configure(parser):
    sp = core_args.add_verb(parser, "diff", "diff a snapshot against live json/")
    sp.add_argument("name", help="substring or full dirname of a backup")
    sp.add_argument("--out", metavar="PATH", help="forward output to the diff tool")
    sp.add_argument("--no-detail", action="store_true",
                    help="skip field-level value diffs (row/id only)")
    sp.add_argument("--sample", type=int, default=20,
                    help="max changed rows shown per file (default 20)")


def run(args):
    snaps = [s for s in _shared.list_snaps() if args.name in s.name]
    if not snaps:
        out.error(f"ERR no backup matches '{args.name}'", exit_code=2)
    if len(snaps) > 1:
        out.emit("multiple backups match; be more specific:")
        for s in snaps:
            out.emit(f"  {s.kind} {s.name}")
        return 1
    snap = snaps[0]
    forward = ["run", "--left", str(snap.path), "--right", str(paths.JSON_DIR)]
    if not getattr(args, "no_detail", False):
        forward += ["--detail", "--sample", str(getattr(args, "sample", 20))]
    if getattr(args, "out", None):
        forward += ["--out", args.out]
    r = proc.run_tool("diff", *forward, check=False)
    return r.returncode
