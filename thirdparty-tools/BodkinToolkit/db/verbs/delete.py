"""db delete — remove a row (destructive)."""
from __future__ import annotations

from ...core import out, prompt
from .. import helpers, storage
from ..schema_loader import load_active


def configure(parser):
    sp = helpers.add_verb(parser, "delete", "remove a row (destructive)")
    sp.add_argument("table")
    sp.add_argument("--id", type=int, required=True)


def run(args):
    schema = load_active()
    schema.require_table(args.table)
    pk = schema.primary_key(args.table)

    rows = storage.load_rows(args.table)
    idx = next((i for i, r in enumerate(rows) if r.get(pk) == args.id), None)
    if idx is None:
        out.error(f"ERR table '{args.table}' has no row with id={args.id}")

    yes = getattr(args, "yes", False)
    try:
        prompt.confirm_destructive(
            f"Delete row id={args.id} from table '{args.table}'?", yes_flag=yes
        )
    except prompt.Cancelled as e:
        out.error(f"ERR {e}")

    rows.pop(idx)
    storage.save_rows(args.table, rows)
