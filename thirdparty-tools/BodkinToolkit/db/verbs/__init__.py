"""One module per `db` verb. Each exposes ``configure(parser)`` and
``run(args)``."""
from . import get, all_, count, next_id, find, put, patch, delete, load, dump, schema

VERBS = {
    "get": get,
    "all": all_,
    "count": count,
    "next-id": next_id,
    "find": find,
    "put": put,
    "patch": patch,
    "delete": delete,
    "load": load,
    "dump": dump,
    "schema": schema,
}

__all__ = ["VERBS"]
