"""import — game JSON -> db rows.

Inbound translation step. Reads game-side JSON from v3/world/json/ and writes
the equivalent rows to db via the bulk `db load` primitive (one call per
table, O(N)).

Run with no args or `?` for the capability summary.
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "translate game JSON files into db rows"

_VERB_HELP = [
    ("json", "import every JSON table from a directory (default: repo json/)"),
    ("one", "import a single table from one JSON file"),
]
_EXAMPLES = [
    "import json",
    "import json --from /path/to/json",
    "import one ammunition --from json/AmmunitionsJson.json",
    "import json --yes",
]


def build():
    parser = core_args.build_parser("import", _PURPOSE)
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
        VERBS[verb].run(args)
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")
    except proc.ToolFailed as e:
        out.error(f"ERR {e}")
    finally:
        out.close_sink()


if __name__ == "__main__":
    main(sys.argv[1:])
