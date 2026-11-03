"""check_patch — compare live json/ to a chosen backup and emit diagnostics."""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "diagnose whether live json/ actually differs from a backup"
_VERB_HELP = [("run", "compare live json/ to a backup and report signals")]
_EXAMPLES = ["check_patch run", "check_patch run --backup preedit"]


def build():
    parser = core_args.build_parser("check_patch", _PURPOSE)
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
