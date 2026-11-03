"""export — db rows -> game JSON. Inverse of import.

Reads rows from db (via `db dump`), rebuilds each game JSON table, and
writes the files either to a chosen directory (--out) or back into the repo
json/ (--in-place, with a light backup first).
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "rebuild game JSON files from db rows"

_VERB_HELP = [
    ("run", "rebuild every table to a directory (--out) or in place (--in-place)"),
    ("one", "rebuild a single table to a file"),
]
_EXAMPLES = [
    "export run --out json_out",
    "export run --in-place",
    "export one ammunition --out json_out/AmmunitionsJson.json",
]


def build():
    parser = core_args.build_parser("export", _PURPOSE)
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
        VERBS[verb].run(args)
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")
    except proc.ToolFailed as e:
        out.error(f"ERR {e}")
    finally:
        out.close_sink()


if __name__ == "__main__":
    main(sys.argv[1:])
