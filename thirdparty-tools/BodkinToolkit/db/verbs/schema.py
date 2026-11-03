"""db schema — inspect and evolve the schema.

Sub-commands: show | add-field | rename-field | change-type | deprecate | bump
Every mutating sub-command writes the next vN+1.yml full snapshot.
"""
from __future__ import annotations

import sys

from ...core import out
from .. import schema_loader
from ..schema_loader import (
    SUPPORTED_TYPES,
    SchemaError,
    clone_tables,
    load_active,
    load_version,
    next_version,
    supported_cast,
    write_snapshot,
)


def configure(parser):
    from .. import helpers
    sp = helpers.add_verb(parser, "schema",
                          "show | add-field | rename-field | change-type | deprecate | bump")
    sub = sp.add_subparsers(dest="schema_cmd")

    p_show = sub.add_parser("show", help="print the active schema (or --version vN)")
    p_show.add_argument("--version", metavar="vN")

    p_add = sub.add_parser("add-field", help="add a field, bump version")
    p_add.add_argument("table")
    p_add.add_argument("field")
    p_add.add_argument("type", nargs="?", help="int|float|str|bool|list|map")
    p_add.add_argument("--type", dest="type_flag", help="alternative to positional type")
    p_add.add_argument("--default")

    p_ren = sub.add_parser("rename-field", help="rename a field, bump version")
    p_ren.add_argument("table")
    p_ren.add_argument("old")
    p_ren.add_argument("new")

    p_ct = sub.add_parser("change-type", help="change a field's type, bump version")
    p_ct.add_argument("table")
    p_ct.add_argument("field")
    p_ct.add_argument("new_type", metavar="new-type")

    p_dep = sub.add_parser("deprecate", help="mark a field obsolete, bump version")
    p_dep.add_argument("table")
    p_dep.add_argument("field")

    p_bump = sub.add_parser("bump", help="manual version bump, no diff")
    p_bump.add_argument("ver", metavar="vN")
    p_bump.add_argument("--note", required=True)


def run(args):
    cmd = getattr(args, "schema_cmd", None)
    if cmd is None:
        out.error("ERR schema requires a sub-command: "
                  "show | add-field | rename-field | change-type | deprecate | bump")
    {
        "show": _show,
        "add-field": _add_field,
        "rename-field": _rename_field,
        "change-type": _change_type,
        "deprecate": _deprecate,
        "bump": _bump,
    }[cmd](args)


def _show(args):
    schema = load_version(args.version) if args.version else load_active()
    out.emit(schema.path.read_text(encoding="utf-8").rstrip("\n"))


def _add_field(args):
    schema = load_active()
    tbl = schema.require_table(args.table)
    ftype = args.type or args.type_flag
    if not ftype:
        out.error("ERR add-field requires a type (positional or --type)")
    if ftype not in SUPPORTED_TYPES:
        out.error(f"ERR unsupported type '{ftype}'; one of {', '.join(SUPPORTED_TYPES)}")
    if args.field in tbl:
        out.error(f"ERR field '{args.field}' already exists in table '{args.table}'")

    vstr, _ = next_version()
    tables = clone_tables(schema)
    attrs = {"type": ftype, "added_in": vstr}
    if args.default is not None:
        from .. import helpers
        attrs["default"] = helpers.parse_scalar(args.default)
    tables[args.table][args.field] = attrs
    path = write_snapshot(tables, f"add field {args.table}.{args.field} ({ftype})")
    out.emit(vstr)


def _rename_field(args):
    schema = load_active()
    tbl = schema.require_table(args.table)
    if args.old not in tbl:
        out.error(f"ERR field '{args.old}' is not declared in table '{args.table}'")
    if args.new in tbl:
        out.error(f"ERR field '{args.new}' already exists in table '{args.table}'")

    vstr, _ = next_version()
    tables = clone_tables(schema)
    # rebuild table dict preserving order, replacing old key with new
    new_tbl = {}
    for k, v in tables[args.table].items():
        if k == args.old:
            v = dict(v)
            v["renamed_from"] = args.old
            v["renamed_in"] = vstr
            new_tbl[args.new] = v
        else:
            new_tbl[k] = v
    tables[args.table] = new_tbl
    write_snapshot(tables, f"rename {args.table}.{args.old} -> {args.new}")
    out.emit(vstr)


def _change_type(args):
    schema = load_active()
    tbl = schema.require_table(args.table)
    if args.field not in tbl:
        out.error(f"ERR field '{args.field}' is not declared in table '{args.table}'")
    if args.new_type not in SUPPORTED_TYPES:
        out.error(f"ERR unsupported type '{args.new_type}'; one of {', '.join(SUPPORTED_TYPES)}")

    old_type = tbl[args.field].get("type", "str")
    new_type = args.new_type
    vstr, _ = next_version()
    tables = clone_tables(schema)
    attrs = dict(tables[args.table][args.field])
    attrs["prior_type"] = old_type
    attrs["type"] = new_type
    attrs["changed_in"] = vstr
    if old_type == new_type:
        out.error(f"ERR field '{args.field}' is already type '{new_type}'")
    if supported_cast(old_type, new_type):
        attrs["converter"] = "cast"
        attrs["converters"] = {f"{old_type}->{new_type}": "cast"}
    else:
        attrs["manual_fix_required"] = True
        sys.stderr.write(
            f"WARN no auto-conversion {old_type}->{new_type} for "
            f"{args.table}.{args.field}; reads will require a manual data fix\n"
        )
    tables[args.table][args.field] = attrs
    write_snapshot(tables, f"change-type {args.table}.{args.field} {old_type}->{new_type}")
    out.emit(vstr)


def _deprecate(args):
    schema = load_active()
    tbl = schema.require_table(args.table)
    if args.field not in tbl:
        out.error(f"ERR field '{args.field}' is not declared in table '{args.table}'")

    vstr, _ = next_version()
    tables = clone_tables(schema)
    tables[args.table][args.field] = dict(tables[args.table][args.field])
    tables[args.table][args.field]["deprecated_in"] = vstr
    write_snapshot(tables, f"deprecate {args.table}.{args.field}")
    out.emit(vstr)


def _bump(args):
    schema = load_active()
    vstr, vnum = next_version()
    if args.ver != vstr:
        sys.stderr.write(
            f"WARN next version is {vstr}; requested {args.ver} ignored\n"
        )
    tables = clone_tables(schema)
    write_snapshot(tables, args.note)
    out.emit(vstr)
