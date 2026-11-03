"""db — CLI dispatcher.

Storage + schema authority for the v3 toolkit. Depends only on `core`.
Run with no args or `?` for the capability summary.
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt
from .schema_loader import SchemaError
from .verbs import VERBS

_PURPOSE = "field-level CRUD for v3 entity storage"

_VERB_HELP = [
    ("get", "read one or more rows by id or field match"),
    ("all", "dump every row in a table"),
    ("count", "row count"),
    ("next-id", "max(id)+1"),
    ("find", "substring/exact search across fields"),
    ("put", "upsert a row"),
    ("patch", "update existing row (fail if missing)"),
    ("delete", "remove a row (destructive)"),
    ("load", "bulk-replace a table from YAML (stdin/--from)"),
    ("dump", "emit a table as a raw YAML list (machine-readable)"),
    ("schema", "show | add-field | rename-field | change-type | deprecate | bump"),
]

_EXAMPLES = [
    "db get units --id 3",
    "db get units --where type=1 --where role=2",
    "db all ammunition --fields id,name",
    "db find units name \"Browning\"",
    "db put units --set name='Test Unit' --set type=1 --set role=0",
    "db patch ammunition --id 7 --set real_world.ground=5000",
    "db delete units --id 999 --yes",
    "db schema add-field units mobility float --default 0.0",
]


def build():
    parser = core_args.build_parser("db", _PURPOSE)
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
    except SchemaError as e:
        out.error(str(e))
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")
    except BrokenPipeError:
        pass
    finally:
        out.close_sink()


if __name__ == "__main__":
    main(sys.argv[1:])
