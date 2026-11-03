"""link — relationship service.

Computes and persists `link_info` blocks on canonical entities and walks the
entity graph for lookup-style queries. Reads and writes through db.
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "compute and persist link_info; walk the entity graph"

_VERB_HELP = [
    ("show", "compute and print one entity's link_info (no write)"),
    ("touch", "recompute + persist link_info for given (table id) pairs"),
    ("init", "recompute + persist link_info for every canonical row"),
    ("walk", "render an enriched view of an entity and its relations"),
]
_EXAMPLES = [
    "link show units 3",
    "link touch units 3 weapons 6 ammunition 7",
    "link init",
    "link walk units 3 --down-once",
]


def build():
    parser = core_args.build_parser("link", _PURPOSE)
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
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")
    try:
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
