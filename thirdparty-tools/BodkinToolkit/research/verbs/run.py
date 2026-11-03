"""research run — parse research markdown and patch ammunition.real_world."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

import yaml
try:
    from yaml import CSafeLoader as _Loader, CSafeDumper as _Dumper
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader, SafeDumper as _Dumper

from ...core import args as core_args, out, paths, proc
from ..parser import parse_research_md
from ..group_classifier import is_air_defense


def configure(parser):
    sp = core_args.add_verb(parser, "run", "parse research/*.md and patch real_world")
    sp.add_argument("--no-overwrite", dest="overwrite", action="store_false",
                    help="only fill null real_world values")
    sp.add_argument("--dry-run", action="store_true", help="report only, no write")
    sp.set_defaults(overwrite=True)


def _load_all_research() -> Dict[int, Dict[str, Any]]:
    rdir = paths.RESEARCH_DIR
    merged: Dict[int, Dict[str, Any]] = {}
    if not rdir.is_dir():
        return merged
    for path in sorted(rdir.glob("*.md")):
        ad = is_air_defense(path.name)
        for aid, rec in parse_research_md(path).items():
            merged[aid] = {"range": rec["range"], "alt": rec["alt"], "is_air_defense": ad}
    return merged


def _apply(rw: Dict[str, Any], rec: Dict[str, Any], overwrite: bool) -> bool:
    changed = False
    if rec["is_air_defense"]:
        for key, val in (("low_alt", rec["range"]), ("high_alt", rec["alt"])):
            if val is None:
                continue
            if overwrite or rw.get(key) in (None, 0, 0.0):
                if rw.get(key) != val:
                    rw[key] = val
                    changed = True
    else:
        val = rec["range"]
        if val is not None and (overwrite or rw.get("ground") in (None, 0, 0.0)):
            if rw.get("ground") != val:
                rw["ground"] = val
                changed = True
    return changed


def run(args):
    research = _load_all_research()
    out.emit(f"loaded research for {len(research)} ammo ids")
    if not research:
        out.emit(f"WARN no research files under {paths.RESEARCH_DIR}")
        return 0

    r = proc.run_tool("db", "dump", "ammunition", capture=True)
    rows = yaml.load(r.stdout, Loader=_Loader) if r.stdout else []
    by_id = {row.get("id"): row for row in rows}

    matched = changed = skipped = 0
    for aid, rec in research.items():
        row = by_id.get(aid)
        if row is None:
            out.emit(f"WARN ammo id {aid} does not exist in db; skipping")
            skipped += 1
            continue
        matched += 1
        rw = row.get("real_world")
        if not isinstance(rw, dict):
            rw = {"ground": None, "low_alt": None, "high_alt": None}
        if _apply(rw, rec, args.overwrite):
            row["real_world"] = rw
            changed += 1

    if not args.dry_run and changed:
        text = yaml.dump(rows, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                         default_flow_style=False, width=4096)
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False,
                                         encoding="utf-8") as tf:
            tf.write(text)
            tmp = tf.name
        try:
            proc.run_tool("db", "load", "ammunition", "--from", tmp, capture=True)
        finally:
            Path(tmp).unlink(missing_ok=True)

    mode = "DRY-RUN " if args.dry_run else ""
    out.emit(f"{mode}matched {matched}, updated {changed}, missing {skipped}")
    return 1 if skipped else 0
