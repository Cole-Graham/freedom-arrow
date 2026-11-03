"""editor - guided, connected db edits that won't break the game.

Interactive. Pick a unit, then edit its deck membership, price, transport,
armor, mobility, optics, stealth, weapons, modifications and abilities. All
reads/writes go through db; shared child entities prompt clone-or-alter.
"""
from __future__ import annotations

import sys

from ..core import args as core_args
from ..core import out, prompt, proc, ui
from .dbio import Tables
from .resolve import resolve_unit, unit_label
from . import flows

_PURPOSE = "guided unit editor (specs, price, transport, armor, mobility, optics, weapons, mods, abilities)"
_VERB_HELP = [("(interactive)", "run with no verb; optionally --unit <id|name>")]
_EXAMPLES = ["editor", "editor --unit 3", "editor --unit BMP-3 --yes"]


def _unit_menu(t: Tables, unit, yes: bool):
    def nodes():
        s = flows.summarize(t, unit)
        return [
            ui.action_node(f"Specializations   : {s['specs']}", lambda: flows.flow_specializations(t, unit)),
            ui.action_node(f"Price (cost)      : {s['price']}", lambda: flows.flow_price(t, unit)),
            ui.action_node(f"Transport         : {s['transport']}", lambda: flows.flow_transport(t, unit, yes)),
            ui.action_node(f"Armor             : {s['armor']}", lambda: flows.flow_armor(t, unit, yes)),
            ui.action_node(f"Mobility / speed  : {s['mobility']}", lambda: flows.flow_mobility(t, unit, yes)),
            ui.action_node(f"Optics / sensors  : {s['optics']}", lambda: flows.flow_sensors(t, unit, yes)),
            ui.action_node(f"Stealth           : {s['stealth']}", lambda: flows.flow_stealth(t, unit)),
            ui.action_node("Replace weapon    : (turret/squad swap)", lambda: flows.flow_weapon_replace(t, unit, yes)),
            ui.action_node(f"Modifications     : {s['mods']}", lambda: flows.flow_modifications(t, unit, yes)),
            ui.action_node(f"Abilities         : {s['abilities']} ability(s)", lambda: flows.flow_abilities(t, unit, yes)),
        ]
    ui.run_form(f"Edit unit: {unit_label(unit)}", nodes, done_label="< done with this unit")


def main(argv=None):
    parser = core_args.build_parser("editor", _PURPOSE)
    parser.add_argument("--unit", metavar="ID|NAME", help="preselect a unit")
    argv = sys.argv[1:] if argv is None else list(argv)
    # editor is interactive: bare invocation runs the UI. Only `?` shows help.
    if argv and argv[0] == "?":
        core_args.print_help_summary(parser, _PURPOSE, _VERB_HELP, _EXAMPLES)
        return
    args = parser.parse_args(argv)
    yes = getattr(args, "yes", False)

    t = Tables()
    try:
        while True:
            unit = None
            if getattr(args, "unit", None):
                unit = resolve_unit(t, args.unit)
                args.unit = None
                if unit is None:
                    out.emit("  no unit matched; pick interactively.")
            if unit is None:
                q = prompt.text("Pick unit (id or partial name, blank to quit)", default="")
                if not q.strip():
                    break
                unit = resolve_unit(t, q)
                if unit is None:
                    out.emit("  no match")
                    continue
            _unit_menu(t, unit, yes)
            if not prompt.confirm("Edit another unit?", default=False):
                break
    except prompt.Cancelled:
        pass
    finally:
        if t.dirty():
            out.emit("  saving changes to db ...")
            t.flush()
            out.emit("  done. (run export + pack to apply to the game)")
        else:
            out.emit("  no changes.")


if __name__ == "__main__":
    main(sys.argv[1:])
