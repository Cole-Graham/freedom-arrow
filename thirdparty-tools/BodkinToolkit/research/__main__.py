"""research — parse research/*.md tables into ammo real_world blocks."""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc
from .verbs import VERBS

_PURPOSE = "parse research markdown into ammunition real_world ranges"
_VERB_HELP = [("run", "parse every research/*.md and patch real_world in db"),
              ("seed", "generate the research-agent worklist CSV from db")]
_EXAMPLES = ["research run", "research run --no-overwrite", "research run --dry-run"]


def build():
    parser = core_args.build_parser("research", _PURPOSE)
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
