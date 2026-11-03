"""check_patch run — backup vs live json/ plus scale/fingerprint/default signals."""
from __future__ import annotations

import yaml
try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

from ...core import args as core_args, out, paths, prompt, proc
from .. import signals


def configure(parser):
    sp = core_args.add_verb(parser, "run", "compare live json/ to a backup and report")
    sp.add_argument("--backup", metavar="NAME", help="name or substring of a backup")


def _list_snaps(kind=None):
    out_snaps = []
    kinds = [kind] if kind else ["light", "heavy"]
    for k in kinds:
        base = paths.BACKUPS_DIR / k
        if base.is_dir():
            for d in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if d.is_dir():
                    out_snaps.append((k, d.name, d))
    return out_snaps


def _db_rows(table):
    r = proc.run_tool("db", "dump", table, capture=True)
    return (yaml.load(r.stdout, Loader=_Loader) if r.stdout else []) or []


def run(args):
    snaps = _list_snaps()
    if not snaps:
        out.error("ERR no backups found under backups/", exit_code=2)

    if getattr(args, "backup", None):
        matched = [s for s in snaps if args.backup in s[1]]
        if not matched:
            out.error(f"ERR no backup matches '{args.backup}'", exit_code=2)
        if len(matched) > 1:
            out.emit("multiple backups match; be more specific:")
            for k, name, _ in matched:
                out.emit(f"  {k} {name}")
            return 1
        chosen = matched[0]
    elif len(snaps) == 1:
        chosen = snaps[0]
    else:
        chosen = prompt.select_one("Choose a backup to compare against:", snaps,
                                   label_fn=lambda s: f"{s[0]} {s[1]}")

    kind, name, path = chosen
    out.emit(f"Comparing live json/ against {kind} backup '{name}'")
    out.emit("")

    diff_res = proc.run_tool("diff", "run", "--left", str(path),
                             "--right", str(paths.JSON_DIR), check=False, capture=True)
    out.emit(diff_res.stdout.rstrip("\n") if diff_res.stdout else "(diff produced no output)")
    identical = diff_res.returncode == 0

    out.emit("")
    out.emit("Signals:")
    ammo = _db_rows("ammunition")
    options = _db_rows("options")
    sc = signals.scale_signal(ammo)
    fp = signals.fingerprint_count(options)
    anomalies = signals.default_anomalies(options)
    out.emit(f"  ammo rows where current != vanilla (scale applied): {sc}")
    out.emit(f"  options matching author fingerprints {sorted(signals.FINGERPRINTS)}: {fp}")
    if anomalies:
        out.emit(f"  modifications without exactly one default option: {len(anomalies)}")
        for mid, cnt in anomalies[:10]:
            out.emit(f"      modification {mid}: {cnt} default(s)")
    else:
        out.emit("  every modification has exactly one default option")

    out.emit("")
    if identical:
        out.emit("VERDICT: live json/ is BYTE-IDENTICAL to backup; either no edits "
                 "reached json/, or edits net to zero. Run 'export run --in-place' "
                 "after editing.")
    else:
        out.emit("VERDICT: live differs from backup; changes are present.")
    return 0
