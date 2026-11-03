"""Shared import helpers: load a table's JSON, translate, push via db load."""
from __future__ import annotations

import json as _json
import tempfile
from pathlib import Path

import yaml
try:
    from yaml import CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeDumper as _Dumper

from ...core import out, paths, proc
from .. import translate


def load_into_db(table: str, json_path: Path) -> int:
    """Translate one game JSON file and bulk-load it into db. Returns rows."""
    try:
        jrows = _json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        out.error(f"ERR cannot find {json_path}")
    except _json.JSONDecodeError as e:
        out.error(f"ERR {json_path.name}: parse failed at L{e.lineno}")
    rows = translate.translate_table(table, jrows)
    text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=4096)
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(text)
        tmp = tf.name
    try:
        proc.run_tool("db", "load", table, "--from", tmp, capture=True)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return len(rows)


def default_json_dir() -> Path:
    return paths.JSON_DIR
