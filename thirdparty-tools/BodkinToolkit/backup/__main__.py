"""backup — snapshot and restore JSON state (light) and the bundle (heavy)."""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "snapshot and restore JSON state and the game bundle"
_VERB_HELP = [
    ("make", "create a light | heavy | both snapshot"),
    ("restore", "restore json/ or the bundle from a snapshot (destructive)"),
    ("list", "list available snapshots, most recent first"),
    ("diff", "diff a named snapshot against the live json/"),
]
_EXAMPLES = [
    "backup make light --name preedit",
    "backup list",
    "backup restore --kind light --name preedit --yes",
    "backup diff preedit",
]


def build():
    parser = core_args.build_parser("backup", _PURPOSE)
    for mod in VERBS.values():
        mod.configure(parser)
    return parser


def main(argv=None):
    parser = build()
    args = core_args.parse_or_help(parser, _PURPOSE, _VERB_HELP, _EXAMPLES, argv=argv)
    verb = getattr(args, "verb", None)
    if not verb:
        core_args.print_help_summary(parser, _PURPOSE, _VERB_HELP, _EXAMPLES)
        return
    try:
        core_args.resolve_out_target(args)
        rc = VERBS[verb].run(args)
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")
    except proc.ToolFailed as e:
        out.error(f"ERR {e}")
    finally:
        out.close_sink()
    if rc:
        sys.exit(rc)


if __name__ == "__main__":
    main(sys.argv[1:])
