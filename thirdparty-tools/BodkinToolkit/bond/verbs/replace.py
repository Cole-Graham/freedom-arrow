"""bond replace — replace a weapon on a unit, with shared-turret cloning,
ammo plumbing, and a trailing link touch."""
from __future__ import annotations

from ...core import args as core_args, out, prompt, proc
from .. import mutations as M
from ..tables import Tables
from ..affected import affected_pairs


def configure(parser):
    sp = core_args.add_verb(parser, "replace", "replace a weapon on a unit")
    sp.add_argument("--unit", type=int, required=True)
    sp.add_argument("--old-weapon", type=int, required=True, dest="old_weapon")
    sp.add_argument("--new-weapon", type=int, required=True, dest="new_weapon")
    sp.add_argument("--ammo", type=int, action="append", default=[],
                    help="ammunition id to attach to (unit, new-weapon); repeatable")
    sp.add_argument("--no-relink", action="store_true", help="skip the trailing link touch")
    sp.add_argument("--yes", action="store_true",
                    help="auto-confirm shared-turret clone and ammo overwrite")


def _exists(t, table, _id):
    return any(r.get("id") == _id for r in t.get(table))


def run(args):
    t = Tables()
    U, Wold, Wnew = args.unit, args.old_weapon, args.new_weapon
    yes = getattr(args, "yes", False)

    if not _exists(t, "units", U):
        out.error(f"ERR unit {U} not found", exit_code=2)
    if not _exists(t, "weapons", Wold):
        out.error(f"ERR weapon {Wold} not found", exit_code=2)
    if not _exists(t, "weapons", Wnew):
        out.error(f"ERR weapon {Wnew} not found", exit_code=2)

    turret_hits = M.turrets_carrying_weapon_for_unit(t, U, Wold)
    squad_present = any(
        r["unit_id"] == U and r["weapon_id"] == Wold for r in t.get("squad_weapons")
    ) or any(
        r["unit_id"] == U and Wold in (r.get("primary_weapon_id"), r.get("special_weapon_id"))
        for r in t.get("squad_members")
    )

    if not turret_hits and not squad_present:
        out.error(f"ERR weapon {Wold} is not mounted on unit {U} "
                  f"(no turret_weapons or squad rows)", exit_code=2)

    log = []
    swapped_turret_ids = []

    for tid, sharers in turret_hits:
        target_turret = tid
        others = [u for u in sharers if u != U]
        if others:
            prompt.confirm_destructive(
                f"Turret #{tid} is shared with units {others}. Clone it for unit "
                f"#{U} only?", yes_flag=yes)
            new_tid, clog = M.clone_turret_for_unit(t, tid, U)
            log.extend(clog)
            target_turret = new_tid
        log.extend(M.swap_weapon_in_turret(t, target_turret, Wold, Wnew))
        swapped_turret_ids.append(target_turret)

    if squad_present:
        log.extend(M.swap_squad_weapon(t, U, Wold, Wnew))

    # ammo plumbing
    log.extend(M.drop_unit_weapon_ammo(t, U, Wold))
    if args.ammo:
        log.extend(M.attach_unit_weapon_ammo(t, U, Wnew, args.ammo))
    else:
        out.emit(f"  WARN no --ammo given; unit #{U} will have an empty loadout "
                 f"for weapon #{Wnew}")

    t.flush()

    out.emit(f"bond replace: unit #{U} weapon #{Wold} -> #{Wnew}")
    for line in log:
        out.emit(f"  {line}")

    if args.no_relink:
        out.emit("  (--no-relink: skipped link touch)")
        return 0

    pairs = affected_pairs(U, Wold, Wnew, swapped_turret_ids, args.ammo)
    touch_args = ["touch"]
    for table, _id in pairs:
        touch_args += [table, str(_id)]
    r = proc.run_tool("link", *touch_args, check=False, capture=True)
    out.emit("  link touch:")
    for line in (r.stdout or "").rstrip("\n").splitlines():
        out.emit(f"    {line}")
    if r.returncode != 0:
        out.emit("  WARN link touch reported failures; re-run manually if needed")
        return 1
    return 0
