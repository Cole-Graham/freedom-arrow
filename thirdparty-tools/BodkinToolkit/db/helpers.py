"""Shared helpers: --set value parsing and record-block printing."""
from __future__ import annotations

import argparse
import re
from typing import Any, Dict, List, Optional

from ..core import args as core_args
from ..core import out
from . import storage
from .schema_loader import Schema, _MISSING


def add_verb(parser: argparse.ArgumentParser, name: str, help_text: str):
    """Add a verb subparser plus the standard --out/--yes flags.

    The flags use SUPPRESS defaults so they don't clobber values parsed at
    the top level when the user places them before the verb.
    """
    sp = core_args.add_verb(parser, name, help_text)
    sp.add_argument("--out", metavar="PATH", default=argparse.SUPPRESS,
                    help="redirect output to PATH")
    sp.add_argument("--yes", action="store_true", default=argparse.SUPPRESS,
                    help="skip confirmation prompts")
    return sp

_INT_RE = re.compile(r"[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?$|[+-]?\d+[eE][+-]?\d+$"
)


def parse_scalar(raw: str) -> Any:
    """Apply the v3 --set / --where value typing rules.

    single-quoted -> forced str; true/false -> bool; null -> None;
    bare int/float -> numeric; everything else -> str.
    """
    s = raw
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null":
        return None
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    return s


def parse_set(token: str) -> tuple:
    """Split ``key=value`` -> ``(key, parsed_value)``. key may use dot paths."""
    if "=" not in token:
        raise ValueError(f"ERR malformed --set '{token}'; expected key=value")
    key, _, value = token.partition("=")
    key = key.strip()
    if not key:
        raise ValueError(f"ERR malformed --set '{token}'; empty key")
    return key, parse_scalar(value)


def set_nested(row: Dict[str, Any], dotted: str, value: Any) -> None:
    """Assign into a row honoring dot-notation for nested maps."""
    parts = dotted.split(".")
    cur = row
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def project_fields(arg: Optional[str]) -> Optional[List[str]]:
    if not arg:
        return None
    return [f.strip() for f in arg.split(",") if f.strip()]


def emit_record(schema: Schema, table: str, row: Dict[str, Any],
                fields: Optional[List[str]]) -> None:
    """Print one record block: ``key: value`` per line, schema order."""
    if fields is not None:
        names = fields
    elif schema.is_passthrough(table):
        names = list(row.keys())
    else:
        names = schema.field_order(table)
    for name in names:
        val = schema.row_value(table, row, name)
        if val is _MISSING:
            if fields is not None:
                # explicit projection: surface absent field as null
                out.emit(f"{name}: null")
            continue
        out.emit(f"{name}: {storage.format_value(val)}")


def emit_records(schema: Schema, table: str, rows: List[Dict[str, Any]],
                 fields: Optional[List[str]]) -> None:
    for i, row in enumerate(rows):
        if i:
            out.emit()
        emit_record(schema, table, row, fields)
