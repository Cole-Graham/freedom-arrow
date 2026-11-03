"""diff — compare two directories (or files) of game JSON, row by row."""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out
from .verbs import VERBS

_PURPOSE = "row + id-set diff between two JSON directories or files"
_VERB_HELP = [("run", "compare --left and --right (dirs or single files)")]
_EXAMPLES = [
    "diff run --left backups/light/X --right json",
    "diff run --left json --right json_out --detail",
    "diff run --left a.json --right b.json --tolerant",
]


def build():
    parser = core_args.build_parser("diff", _PURPOSE)
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
    core_args.resolve_out_target(args)
    rc = VERBS[verb].run(args)
    out.close_sink()
    if rc:
        sys.exit(rc)


if __name__ == "__main__":
    main(sys.argv[1:])
