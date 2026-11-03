"""Editor flows. Each operates on a selected unit and mutates the Tables cache
(flushed by the caller). Weapon replacement delegates to the `bond` tool via
its front.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..core import out, proc, prompt, ui
from .dbio import Tables, pk_of
from .resolve import resolve, resolve_unit, unit_label
from .shared import clone_or_alter, other_users, unit_name


# ── small helpers ────────────────────────────────────────────────────────────

def _num(v):
    return ui.parse_float if isinstance(v, float) else ui.parse_int


def _value_nodes(row: Dict[str, Any], fields: List[str], mark) -> List[ui.Node]:
    """Build value nodes for the given numeric/scalar fields of a row."""
    nodes = []
    for f in fields:
        if f not in row:
            continue
        cur = row[f]
        parse = ui.parse_float if isinstance(cur, float) else (
            ui.parse_int if isinstance(cur, int) and not isinstance(cur, bool) else
            ui.parse_bool if isinstance(cur, bool) else str)

        def mk(field):
            def getter():
                return row[field]

            def setter(v):
                row[field] = v
                mark()
            return getter, setter
        g, s = mk(f)
        nodes.append(ui.value_node(f, g, s, default=cur, parse=parse))
    return nodes


# ── price + transport ────────────────────────────────────────────────────────

def flow_price(t: Tables, unit: Dict[str, Any]):
    def nodes():
        return [ui.value_node("Cost", lambda: unit.get("cost"),
                              lambda v: (unit.__setitem__("cost", v), t.mark("units")),
                              default=unit.get("cost"), parse=ui.parse_int)]
    ui.run_form(f"Price - {unit['name']}", nodes)


def _unit_avails(t, uid):
    return t.where("specialization_availabilities", UnitId=uid)


def flow_transport(t: Tables, unit: Dict[str, Any], yes=False):
    uid = unit["id"]
    avails = _unit_avails(t, uid)
    if not avails:
        out.emit("  unit has no deck availabilities; add it to a specialization first.")
        return

    def carriers():
        ids = sorted({r["UnitId"] for a in avails
                      for r in t.where("transport_availabilities",
                                       SpecializationAvailabilityId=a["Id"])})
        return ids

    def add_carrier():
        q = prompt.text("Carrier unit (id or partial name)")
        cu = resolve_unit(t, q)
        if not cu:
            out.emit("  no match")
            return
        n = 0
        for a in avails:
            exists = t.where("transport_availabilities",
                             SpecializationAvailabilityId=a["Id"], UnitId=cu["id"])
            if not exists:
                t.add("transport_availabilities", {
                    "Id": t.next_id("transport_availabilities"),
                    "SpecializationAvailabilityId": a["Id"], "UnitId": cu["id"]})
                n += 1
        out.emit(f"  added carrier {cu['name']} to {n} availability slot(s)")

    def remove_carrier():
        ids = carriers()
        if not ids:
            out.emit("  no carriers set")
            return
        chosen = ui.choose_one("Remove which carrier?", ids,
                               label_fn=lambda i: unit_name(t, i))
        if chosen is None:
            return
        n = t.remove("transport_availabilities",
                     lambda r: r["UnitId"] == chosen and any(
                         r["SpecializationAvailabilityId"] == a["Id"] for a in avails))
        out.emit(f"  removed {n} transport row(s)")

    def nodes():
        cur = ", ".join(unit_name(t, i) for i in carriers()) or "(none)"
        return [
            ui.action_node(f"Carriers: {cur}", lambda: None),
            ui.action_node("Add carrier (id or partial name)", add_carrier),
            ui.action_node("Remove carrier", remove_carrier),
        ]
    ui.run_form(f"Transport - {unit['name']}", nodes)


# ── specialization membership ────────────────────────────────────────────────

def flow_specializations(t: Tables, unit: Dict[str, Any]):
    uid = unit["id"]
    specs = t.get("specializations")

    def spec_label(s):
        return f"#{s['Id']}  {s.get('UIName') or s.get('Name')}"

    current_avails = _unit_avails(t, uid)
    current_spec_ids = {a["SpecializationId"] for a in current_avails}
    cur_names = [s.get("UIName") or s.get("Name") for s in specs
                 if s["Id"] in current_spec_ids]
    out.emit(f"  {unit['name']} currently in: "
             + (", ".join(cur_names) if cur_names else "(no specializations)"))

    preselected = [i for i, s in enumerate(specs) if s["Id"] in current_spec_ids]
    chosen = ui.choose_many("Toggle specializations this unit belongs to:",
                            specs, label_fn=spec_label, preselected=preselected)
    if chosen is None:
        return
    chosen_ids = {s["Id"] for s in chosen}

    # add new
    added = removed = 0
    template = current_avails[0] if current_avails else None
    for sid in chosen_ids - current_spec_ids:
        row = {"Id": t.next_id("specialization_availabilities"),
               "SpecializationId": sid, "UnitId": uid}
        for xp in ("MaxAvailabilityXp0", "MaxAvailabilityXp1",
                   "MaxAvailabilityXp2", "MaxAvailabilityXp3"):
            row[xp] = template.get(xp, 1) if template else 1
        t.add("specialization_availabilities", row)
        added += 1
    # remove dropped (cascade transport rows)
    for sid in current_spec_ids - chosen_ids:
        avail_ids = [a["Id"] for a in current_avails if a["SpecializationId"] == sid]
        removed += t.remove("specialization_availabilities",
                            lambda r: r["UnitId"] == uid and r["SpecializationId"] == sid)
        for aid in avail_ids:
            t.remove("transport_availabilities",
                     lambda r: r["SpecializationAvailabilityId"] == aid)
    out.emit(f"  specs updated: +{added} -{removed}")


# ── armor / mobility / sensors / stealth ─────────────────────────────────────

ARMOR_FIELDS = ["ArmorValue", "MaxHealthPoints",
                "KinArmorFront", "KinArmorRear", "KinArmorSides", "KinArmorTop",
                "HeatArmorFront", "HeatArmorRear", "HeatArmorSides", "HeatArmorTop"]
MOBILITY_GROUND = ["MaxSpeedRoad", "MaxCrossCountrySpeed", "MaxSpeedReverse",
                   "MaxSpeedWater", "Acceleration", "TurnRate", "Agility",
                   "IsAmphibious", "Weight"]
MOBILITY_AIR = ["MaxSpeedRoad", "Agility", "ClimbRate", "TurnRate", "Acceleration",
                "LoiteringTime", "IsAfterburner", "AfterBurningLoiteringTime",
                "IsChangeAltitude"]
FLY_FIELDS = ["MinSpeed", "CornerSpeed", "MaxSpeed", "AfterburnSpeed",
              "Acceleration", "Deceleration", "MaxRoll"]
SENSOR_FIELDS = ["OpticsGround", "OpticsLowAltitude", "OpticsHighAltitude"]


def _edit_child(t, unit, bridge, ref_field, ref_table, fields, title, yes=False,
                extra_builder=None):
    uid = unit["id"]
    links = t.where(bridge, UnitId=uid)
    if not links:
        out.emit(f"  unit has no {ref_table} link.")
        return
    if len(links) == 1:
        link = links[0]
    else:
        link = ui.choose_one(f"Which {ref_table} link?", links,
                             label_fn=lambda r: f"{ref_field}={r[ref_field]}")
        if link is None:
            return
    ref_id = clone_or_alter(t, ref_table, link[ref_field], bridge, ref_field, uid, yes=yes)
    row = t.by_id(ref_table, ref_id)

    def nodes():
        ns = _value_nodes(row, fields, lambda: t.mark(ref_table))
        if extra_builder:
            ns += extra_builder(row)
        return ns
    ui.run_form(f"{title} - {unit['name']} ({ref_table} #{ref_id})", nodes)


def flow_armor(t, unit, yes=False):
    _edit_child(t, unit, "unit_armors", "ArmorId", "armors", ARMOR_FIELDS, "Armor", yes)


def flow_sensors(t, unit, yes=False):
    _edit_child(t, unit, "sensor_units", "SensorId", "sensors", SENSOR_FIELDS, "Optics", yes)


def flow_stealth(t, unit):
    def nodes():
        return [ui.value_node("Stealth", lambda: unit.get("stealth"),
                              lambda v: (unit.__setitem__("stealth", v), t.mark("units")),
                              default=unit.get("stealth"), parse=ui.parse_float)]
    ui.run_form(f"Stealth - {unit['name']}", nodes)


def flow_mobility(t, unit, yes=False):
    uid = unit["id"]
    links = t.where("unit_propulsions", UnitId=uid)
    if not links:
        out.emit("  unit has no mobility link.")
        return
    link = links[0] if len(links) == 1 else ui.choose_one(
        "Which mobility link?", links, label_fn=lambda r: f"MobilityId={r['MobilityId']}")
    if link is None:
        return
    mob_id = clone_or_alter(t, "mobility", link["MobilityId"], "unit_propulsions",
                            "MobilityId", uid, yes=yes)
    mob = t.by_id("mobility", mob_id)
    is_aircraft = bool(mob.get("FlyPresetId")) or bool(mob.get("FlyPreset"))
    fields = MOBILITY_AIR if is_aircraft else MOBILITY_GROUND
    out.emit(f"  mobility #{mob_id} detected as {'AIRCRAFT' if is_aircraft else 'GROUND'}")

    def fly_submenu(row):
        if not is_aircraft or not row.get("FlyPresetId"):
            return []
        fp = t.by_id("fly_presets", row["FlyPresetId"])
        if not fp:
            return []
        return [ui.submenu_node(
            "Flight model (fly preset)",
            lambda: _value_nodes(fp, FLY_FIELDS, lambda: t.mark("fly_presets")),
            summary=lambda: fp.get("Name", ""))]

    def nodes():
        return _value_nodes(mob, fields, lambda: t.mark("mobility")) + fly_submenu(mob)
    ui.run_form(f"Mobility - {unit['name']}", nodes)


# ── abilities ────────────────────────────────────────────────────────────────

ABILITY_QTY_FIELDS = ["SmokeAmmunitionQuantity", "APSQuantity", "DecoyQuantity",
                      "ResupplyPoints", "SprintDuration", "SmokeCooldown",
                      "APSCooldown", "DecoyCooldown"]


def flow_abilities(t, unit, yes=False):
    uid = unit["id"]
    links = t.where("unit_abilities", UnitId=uid)
    if not links:
        out.emit("  unit has no abilities.")
        return

    def ability_label(link):
        ab = t.by_id("abilities", link["AbilityId"])
        return f"#{link['AbilityId']}  {ab.get('Name') if ab else '?'}"

    def pick_and_edit():
        link = ui.choose_one("Edit which ability?", links, label_fn=ability_label)
        if link is None:
            return
        aid = clone_or_alter(t, "abilities", link["AbilityId"], "unit_abilities",
                             "AbilityId", uid, yes=yes)
        ab = t.by_id("abilities", aid)
        present = [f for f in ABILITY_QTY_FIELDS if f in ab]
        if not present:
            out.emit("  (this ability has no editable quantity/cooldown fields)")
        out.emit("  note: 'limitless' sentinel not yet confirmed - set explicit numbers.")

        def nodes():
            return _value_nodes(ab, present, lambda: t.mark("abilities"))
        ui.run_form(f"Ability {ab.get('Name')} - {unit['name']}", nodes)

    def view():
        for link in links:
            ab = t.by_id("abilities", link["AbilityId"]) or {}
            qty = {f: ab.get(f) for f in ABILITY_QTY_FIELDS if f in ab and ab.get(f) not in (0, None)}
            out.emit(f"  #{link['AbilityId']:<4} {ab.get('Name','?'):<28} {qty if qty else ''}")

    def nodes():
        return [ui.action_node("View all abilities", view),
                ui.action_node("Edit an ability (quantities / cooldowns)", pick_and_edit)]
    ui.run_form(f"Abilities - {unit['name']}", nodes)


# ── weapon replacement (delegates to bond) ───────────────────────────────────

def _unit_weapon_ids(t, uid):
    ids = set()
    for r in t.where("weapon_ammunitions", unit_id=uid):
        ids.add(r["weapon_id"])
    for r in t.where("squad_weapons", unit_id=uid):
        ids.add(r["weapon_id"])
    for r in t.where("squad_members", unit_id=uid):
        for k in ("primary_weapon_id", "special_weapon_id"):
            if r.get(k):
                ids.add(r[k])
    turret_ids = {r["turret_id"] for r in t.where("turret_units", unit_id=uid)}
    for r in t.get("turret_weapons"):
        if r["turret_id"] in turret_ids:
            ids.add(r["weapon_id"])
    return sorted(i for i in ids if i)


def _wname(t, wid):
    w = t.by_id("weapons", wid)
    return w.get("name") if w else f"#{wid}"


def flow_weapon_replace(t, unit, yes=False):
    uid = unit["id"]
    wids = _unit_weapon_ids(t, uid)
    if not wids:
        out.emit("  no weapons found on this unit.")
        return
    old = ui.choose_one("Replace which weapon?", wids,
                        label_fn=lambda i: f"#{i}  {_wname(t, i)}")
    if old is None:
        return
    old_id = old
    new_q = prompt.text("New weapon: id or partial name (blank = cancel)", default="")
    if not new_q.strip():
        return
    new = resolve(t, "weapons", new_q)
    if not new:
        out.emit("  no match for new weapon")
        return
    ammo_ids = []
    while True:
        aq = prompt.text("Add ammo (id or partial name, blank to finish)", default="")
        if not aq.strip():
            break
        a = resolve(t, "ammunition", aq)
        if a:
            ammo_ids.append(str(a["id"]))
            out.emit(f"    + {a['name']}")
    # editor cache may hold edits; flush so bond reads consistent db
    t.flush()
    args = ["replace", "--unit", str(uid), "--old-weapon", str(old_id),
            "--new-weapon", str(new["id"])]
    for a in ammo_ids:
        args += ["--ammo", a]
    if yes:
        args.append("--yes")
    out.emit(f"  delegating to bond: {' '.join(args)}")
    proc.run_tool("bond", *args, check=False)


# ── modifications / options ──────────────────────────────────────────────────

OPTION_SCALARS = ["ui_name", "order", "is_default", "cost", "stealth_override",
                  "armor_id", "mobility_id", "main_sensor_id", "extra_sensor_id",
                  "replace_unit_id"]


def _turret_name(t, tid):
    tr = t.by_id("turrets", tid)
    return tr.get("name") if tr else f"#{tid}"


def _edit_option(t, opt, unit):
    uid = unit["id"]
    unit_mod_ids = {m["id"] for m in t.where("modifications", unit_id=uid)}

    def unit_options():
        return [o for o in t.get("options") if o.get("modification_id") in unit_mod_ids]

    def slot_usage():
        """slot -> [(option_label, turret_id)] across THIS UNIT's OTHER options."""
        usage = {}
        for o in unit_options():
            if o is opt:
                continue
            for s, tid in (o.get("turret_overrides") or {}).items():
                usage.setdefault(int(s), []).append((o.get("ui_name") or f"#{o['id']}", tid))
        return usage

    def turret_overrides_menu():
        def show_usage():
            usage = slot_usage()
            here = {int(s) for s in (opt.get("turret_overrides") or {})}
            out.emit(f"  turret slots used by OTHER options on {unit['name']} only:")
            if not usage:
                out.emit("    (none - no other option on this unit overrides turrets)")
            for s in sorted(usage):
                tag = "also in THIS option" if s in here else "NOT in this option"
                names = ", ".join(sorted({f"{n} -> {_turret_name(t, tid)}"
                                          for n, tid in usage[s]})[:6])
                out.emit(f"    slot {s} ({tag}): {names}")

        def set_slot():
            usage = slot_usage()
            ov = dict(opt.get("turret_overrides") or {})
            relevant = sorted(set(list(usage.keys()) + [int(s) for s in ov.keys()]))
            menu = [f"slot {s}" for s in relevant] + ["(other slot number)"]
            pick = ui.choose_one("Which turret slot?", menu, label_fn=str)
            if pick is None:
                return
            if pick == "(other slot number)":
                raw = prompt.text("Slot number 0-20 (blank = cancel)", default="")
                if not raw.strip().isdigit():
                    return
                slot = int(raw)
            else:
                slot = int(pick.split()[1])
            q = prompt.text("Turret: id or partial name (blank = clear this slot)", default="")
            if not q.strip():
                if slot in ov or str(slot) in ov:
                    ov.pop(slot, None)
                    ov.pop(str(slot), None)
                    opt["turret_overrides"] = ov
                    t.mark("options")
                    out.emit(f"  cleared slot {slot}")
                return
            tr = resolve(t, "turrets", q)
            if not tr:
                out.emit("  no turret match")
                return
            ov[slot] = tr["id"]
            opt["turret_overrides"] = ov
            t.mark("options")
            out.emit(f"  slot {slot} -> turret #{tr['id']} {tr.get('name')}")

        def nodes():
            ns = [ui.action_node("Show turret-slot usage on THIS unit", show_usage),
                  ui.action_node("Set / clear a slot (search turret by name)", set_slot)]
            for s, tid in sorted((opt.get("turret_overrides") or {}).items(),
                                 key=lambda kv: int(kv[0])):
                ns.append(ui.action_node(f"slot {s}: #{tid} {_turret_name(t, tid)}", set_slot))
            return ns
        return nodes()          # builder for submenu_node (run_form drives it)

    def nodes():
        ns = _value_nodes(opt, OPTION_SCALARS, lambda: t.mark("options"))
        ns.append(ui.submenu_node(
            "Turret overrides", turret_overrides_menu,
            summary=lambda: f"{len(opt.get('turret_overrides') or {})} set"))
        return ns
    ui.run_form(f"Option #{opt['id']} {opt.get('ui_name','')}", nodes)


def flow_modifications(t, unit, yes=False):
    uid = unit["id"]

    def mods():
        return t.where("modifications", unit_id=uid)

    def new_slot():
        name = prompt.text("New modification slot ui_name")
        mid = t.next_id("modifications")
        order = max([m.get("order", 0) for m in mods()], default=-1) + 1
        t.add("modifications", {"id": mid, "unit_id": uid, "ui_name": name,
                                "type": 0, "order": order})
        out.emit(f"  created modification slot #{mid} '{name}'")

    def options_of(mid):
        return t.where("options", modification_id=mid)

    def new_option(mid):
        how = ui.choose_one("New option from:", ["empty template", "clone existing"],
                            label_fn=str)
        if how is None:
            return
        oid = t.next_id("options")
        if how == "clone existing":
            opts = options_of(mid) or t.get("options")
            src = ui.choose_one("Clone which option?", opts,
                                label_fn=lambda o: f"#{o['id']} {o.get('ui_name','')}")
            if src is None:
                return
            row = dict(src)
            row["id"] = oid
            row["modification_id"] = mid
            row["ui_name"] = (src.get("ui_name") or "option") + " (copy)"
        else:
            row = {"id": oid, "modification_id": mid, "ui_name": "custom_option_empty",
                   "order": len(options_of(mid)), "is_default": False, "cost": 0}
        t.add("options", row)
        out.emit(f"  created option #{oid}")

    def nodes():
        ns = [ui.action_node("New modification slot", new_slot)]
        for m in mods():
            ns.append(ui.submenu_node(
                f"Slot #{m['id']} {m.get('ui_name','')}",
                (lambda mm: (lambda: _mod_children(t, mm, unit, options_of, new_option)))(m),
                summary=lambda mm=m: f"{len(options_of(mm['id']))} option(s)"))
        return ns
    ui.run_form(f"Modifications - {unit['name']}", nodes)


def _mod_children(t, m, unit, options_of, new_option):
    mid = m["id"]
    return [ui.action_node("New option (empty / clone)", lambda: new_option(mid))] + [
        ui.action_node(f"Edit option #{o['id']} {o.get('ui_name','')}",
                       (lambda oo: (lambda: _edit_option(t, oo, unit)))(o))
        for o in options_of(mid)]


# ── current-value summary (for the unit menu table) ──────────────────────────

def _ref_via(t, bridge, ref_field, ref_table, uid):
    links = t.where(bridge, UnitId=uid)
    return t.by_id(ref_table, links[0][ref_field]) if links else None


def summarize(t, unit) -> dict:
    """One-line current-value summaries per category for the unit menu."""
    uid = unit["id"]
    s = {"price": unit.get("cost"), "stealth": unit.get("stealth")}

    arm = _ref_via(t, "unit_armors", "ArmorId", "armors", uid)
    s["armor"] = (f"HP={arm.get('MaxHealthPoints')} kin F/S/R="
                  f"{arm.get('KinArmorFront')}/{arm.get('KinArmorSides')}/{arm.get('KinArmorRear')}"
                  if arm else "-")

    mob = _ref_via(t, "unit_propulsions", "MobilityId", "mobility", uid)
    if mob:
        if mob.get("FlyPresetId") or mob.get("FlyPreset"):
            s["mobility"] = f"AIR spd={mob.get('MaxSpeedRoad')}"
        else:
            s["mobility"] = f"road={mob.get('MaxSpeedRoad')} ccs={mob.get('MaxCrossCountrySpeed')}"
    else:
        s["mobility"] = "-"

    sen = _ref_via(t, "sensor_units", "SensorId", "sensors", uid)
    s["optics"] = (f"G={sen.get('OpticsGround')} L={sen.get('OpticsLowAltitude')} "
                   f"H={sen.get('OpticsHighAltitude')}" if sen else "-")

    avails = t.where("specialization_availabilities", UnitId=uid)
    names = []
    for a in avails:
        sp = t.by_id("specializations", a["SpecializationId"]) or {}
        n = sp.get("UIName") or sp.get("Name")
        if n:
            names.append(n)
    s["specs"] = ", ".join(names) if names else "-"

    carriers = {r["UnitId"] for a in avails
                for r in t.where("transport_availabilities", SpecializationAvailabilityId=a["Id"])}
    s["transport"] = f"{len(carriers)} carrier(s)"
    s["abilities"] = f"{len(t.where('unit_abilities', UnitId=uid))}"
    s["mods"] = f"{len(t.where('modifications', unit_id=uid))} slot(s)"
    return s
