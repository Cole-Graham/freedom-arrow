"""diff run — summary + id diffs (+ optional field detail) for two JSON trees."""
from __future__ import annotations

from pathlib import Path
from typing import List

from ...core import args as core_args, out
from .. import compare


def configure(parser):
    sp = core_args.add_verb(parser, "run", "compare --left and --right")
    sp.add_argument("--left", required=True, metavar="DIR|FILE")
    sp.add_argument("--right", required=True, metavar="DIR|FILE")
    sp.add_argument("--only", nargs="*", default=[], metavar="NAME",
                    help="restrict to these file basenames (without .json)")
    sp.add_argument("--sample", type=int, default=10, help="max ids printed per group")
    sp.add_argument("--tolerant", action="store_true", help="repair truncated JSON tails")
    sp.add_argument("--detail", action="store_true", help="per-id field-level diff")


def _file_pairs(left: Path, right: Path, only):
    if left.is_file() or right.is_file():
        return [(left.name, left, right)]
    only_set = {f"{n}.json" for n in only} if only else None
    names = sorted(p.name for p in left.glob("*.json"))
    pairs = []
    for n in names:
        if only_set and n not in only_set:
            continue
        pairs.append((n, left / n, right / n))
    return pairs


def _print_ids(label, ids, rows, cap):
    if not ids:
        return
    by_id = {r["Id"]: r for r in rows if "Id" in r}
    s = sorted(ids)
    out.emit(f"    {label} ({len(ids)} total):")
    for i in s[:cap]:
        out.emit(f"      id={i:>6}  {compare.summarize_row(by_id.get(i, {}))}")
    if len(s) > cap:
        out.emit(f"      ... (+{len(s) - cap} more)")


def run(args):
    left, right = Path(args.left), Path(args.right)
    if not left.exists():
        out.error(f"ERR {left} not found", exit_code=2)
    if not right.exists():
        out.error(f"ERR {right} not found", exit_code=2)

    out.emit(f"LEFT : {left}")
    out.emit(f"RIGHT: {right}")
    out.emit("")
    out.emit(f"  {'file':<32} {'left':>7} {'right':>7} {'Δrows':>6}  notes")
    out.emit(f"  {'-'*32} {'-'*7} {'-'*7} {'-'*6}  {'-'*20}")

    total_l = total_r = 0
    diffs = []
    field_diffs = []
    bad = []
    for name, lp, rp in _file_pairs(left, right, args.only):
        l = compare.load_json(lp, args.tolerant)
        r = compare.load_json(rp, args.tolerant)
        if isinstance(l, Exception) or l is None:
            bad.append(f"{name} (LEFT unreadable)")
            continue
        if isinstance(r, Exception) or r is None:
            bad.append(f"{name} (RIGHT unreadable)")
            continue
        nl, nr = len(l), len(r)
        total_l += nl
        total_r += nr
        delta = nr - nl
        flag = "" if delta == 0 else " WARN"
        out.emit(f"  {name:<32} {nl:>7} {nr:>7} {delta:>+6}{flag}")
        if l and "Id" in l[0]:
            miss, extra = compare.id_diff(l, r)
            if miss or extra:
                diffs.append((name, l, r, miss, extra))
            if args.detail:
                fd = compare.field_diff(l, r)
                if fd:
                    field_diffs.append((name, fd))

    out.emit("")
    out.emit(f"  {'TOTAL':<32} {total_l:>7} {total_r:>7} {total_r - total_l:>+6}")

    if bad:
        out.emit("")
        out.emit("  Could not parse:")
        for b in bad:
            out.emit(f"    {b}")

    if diffs:
        out.emit("")
        out.emit("  Per-file id diffs:")
        for name, l, r, miss, extra in diffs:
            out.emit(f"  --- {name} ---")
            _print_ids("missing in RIGHT (lost rows)", miss, l, args.sample)
            _print_ids("extra in RIGHT (forged rows)", extra, r, args.sample)

    if field_diffs:
        out.emit("")
        out.emit("  Field-level diffs (changed rows):")
        for name, fd in field_diffs:
            out.emit(f"  --- {name} ({len(fd)} changed) ---")
            for i, changes in fd[:args.sample]:
                out.emit(f"      id={i}:")
                for fld, lv, rv in changes:
                    out.emit(f"        {fld}: {compare.fmt_val(lv)} -> {compare.fmt_val(rv)}")
            if len(fd) > args.sample:
                out.emit(f"      ... (+{len(fd) - args.sample} more changed rows)")

    return 0 if (total_l == total_r and not diffs and not field_diffs) else 1
