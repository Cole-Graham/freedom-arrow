"""bond — bridge-table mutations with consistency.

v3 day one scope: the `replace` verb (replace a weapon on a unit, with
shared-turret cloning and ammo plumbing), followed by `link touch` on the
affected canonical entities.
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "mutate bridge tables (weapon replacement) with link consistency"
_VERB_HELP = [("replace", "replace a weapon on a unit (turret or squad), plumb ammo")]
_EXAMPLES = [
    "bond replace --unit 3 --old-weapon 6 --new-weapon 270 --ammo 7 --ammo 177",
    "bond replace --unit 3 --old-weapon 6 --new-weapon 270 --yes --no-relink",
]


def build():
    parser = core_args.build_parser("bond", _PURPOSE)
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
