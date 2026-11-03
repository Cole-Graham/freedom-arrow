"""research seed — generate/refresh the agent worklist CSV from db.

Enumerates every (unit · weapon · ammunition) combination and writes one row
per distinct Name into research/agents/research_data.csv for the background
research agent to fill. Vehicle units use their name; squad/infantry units use
the literal `infantry` placeholder. Existing rows (with data the agent already
filled) are preserved by Name; only new Names are added.
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml
try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

from ...core import args as core_args, out, paths, proc

COLUMNS = ["Name", "RangeGround", "RangeLow", "RangeHigh", "MuzzleEnergyJ",
           "FrontalAirResistance", "Confidence", "Date", "Sources"]


def configure(parser):
    sp = core_args.add_verb(parser, "seed",
                            "generate the agent worklist CSV (Names) from db")
    sp.add_argument("--out", dest="out_file", metavar="FILE",
                    help="output CSV (default: research/agents/research_data.csv)")


def _dump(table):
    r = proc.run_tool("db", "dump", table, capture=True)
    return (yaml.load(r.stdout, Loader=_Loader) if r.stdout else []) or []


def _agents_dir() -> Path:
    return paths.tool_root("research") / "agents"


def run(args):
    units = {r["id"]: r for r in _dump("units")}
    weapons = {r["id"]: r for r in _dump("weapons")}
    ammo = {r["id"]: r for r in _dump("ammunition")}
    wa = _dump("weapon_ammunitions")

    # infantry = units that field squads
    infantry = {r["unit_id"] for r in _dump("squad_members")} \
        | {r["unit_id"] for r in _dump("squad_weapons")}

    names = []
    seen = set()
    for r in wa:
        u, w, a = r.get("unit_id"), r.get("weapon_id"), r.get("ammunition_id")
        if w not in weapons or a not in ammo:
            continue
        unit_part = "infantry" if u in infantry else (units.get(u, {}).get("name") or f"unit{u}")
        name = f"{unit_part} | {weapons[w].get('name')} | {ammo[a].get('name')}"
        if name not in seen:
            seen.add(name)
            names.append(name)
    names.sort()

    out_path = Path(args.out_file) if getattr(args, "out_file", None) \
        else _agents_dir() / "research_data.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # preserve existing rows by Name
    existing = {}
    if out_path.exists():
        with out_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("Name"):
                    existing[row["Name"]] = row

    kept = sum(1 for n in names if n in existing)
    added = 0
    rows = []
    for n in names:
        if n in existing:
            rows.append(existing.pop(n))
        else:
            rows.append({c: "" for c in COLUMNS} | {"Name": n})
            added += 1
    # keep any leftover existing rows whose Name is no longer generated (stale, not deleted)
    stale = list(existing.values())
    rows.extend(stale)

    tmp = out_path.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        wri.writeheader()
        wri.writerows(rows)
    tmp.replace(out_path)

    out.emit(f"  worklist: {out_path}")
    out.emit(f"  {len(names)} distinct names ({added} new, {kept} preserved, "
             f"{len(stale)} stale kept)")
    return 0
