"""Interactive launcher for the Broken Arrow v3 modding toolkit.

Nested menus, optional arrow-key navigation on Windows (msvcrt), graceful
fall-back to typed-key entry elsewhere. Every item dispatches to a v3 tool
through its single front (`core.proc.run_tool`) or to a pipeline front
(`core.proc.run_entry`). No tool internals are imported.
"""
from __future__ import annotations

import os
import sys

from ..core import out, paths, proc, prompt
from . import placement

PY = sys.executable


# ---------------------------------------------------------------------------
# Key-reading layer (ported from the legacy menu)
# ---------------------------------------------------------------------------

def _msvcrt_getch():
    import msvcrt
    ch = msvcrt.getch()
    if ch in (b'\x00', b'\xe0'):
        code = msvcrt.getch()
        return {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right'}.get(code, '')
    if ch == b'\r':
        return 'enter'
    if ch == b'\x1b':
        return 'esc'
    try:
        return ch.decode('utf-8', errors='ignore').lower()
    except Exception:
        return ''


def _arrow_keys_available() -> bool:
    if os.name != 'nt':
        return False
    try:
        import msvcrt  # noqa: F401
        return sys.stdin.isatty()
    except Exception:
        return False


ARROW_KEYS = _arrow_keys_available()
BAR = "=" * 70


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def header(title: str, breadcrumb: str = ''):
    clear()
    print(BAR)
    print("  BROKEN ARROW MODDING PIPELINE")
    if breadcrumb:
        print(f"  > {breadcrumb}")
    if title:
        print(f"  {title}")
    print(BAR)
    print()


def pause():
    print()
    try:
        input("  [enter to return to menu] ")
    except (EOFError, KeyboardInterrupt):
        pass


def ask(label: str, default: str = "") -> str:
    try:
        raw = input(f"  {label}{f' [{default}]' if default else ''}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return raw or default


# ---------------------------------------------------------------------------
# Invocation — tools only via their front; pipelines via their entry script
# ---------------------------------------------------------------------------

def tool(name: str, *args: str) -> int:
    out.emit(f"  $ {name} {' '.join(args)}")
    print()
    try:
        return proc.run_tool(name, *args, check=False).returncode
    except KeyboardInterrupt:
        print("\n  (interrupted)")
        return 130


def pipeline(name: str, *args: str) -> int:
    entry = paths.V3_ROOT / "actions" / name / f"{name}.py"
    out.emit(f"  $ {name} {' '.join(args)}")
    print()
    try:
        return proc.run_entry(entry, *args, check=False).returncode
    except KeyboardInterrupt:
        print("\n  (interrupted)")
        return 130


# Dispatchers ---------------------------------------------------------------

def _run(fn):
    def wrapped():
        fn()
        pause()
    return wrapped


def do_backup_make():
    kind = ask("backup kind [light/heavy/both]", "both")
    name = ask("name prefix (optional)")
    args = ["make", kind]
    if name:
        args += ["--name", name]
    tool("backup", *args)


def do_walk():
    table = ask("table (units/weapons/ammunition)", "units")
    eid = ask("id")
    if eid:
        tool("link", "walk", table, eid, "--down-once")


def do_show():
    table = ask("table (units/weapons/ammunition/turrets/modifications/options)", "units")
    eid = ask("id")
    if eid:
        tool("link", "show", table, eid)


def do_bond_replace():
    u = ask("unit id")
    old = ask("old weapon id")
    new = ask("new weapon id")
    if not (u and old and new):
        out.emit("  (cancelled — unit/old/new are required)")
        return
    ammo = ask("ammo ids (space-separated, optional)")
    args = ["replace", "--unit", u, "--old-weapon", old, "--new-weapon", new]
    for a in ammo.split():
        args += ["--ammo", a]
    tool("bond", *args)


def do_diff():
    left = ask("left dir/file", str(paths.JSON_DIR))
    right = ask("right dir/file", str(paths.WORLD_DIR / "json_out"))
    tool("diff", "run", "--left", left, "--right", right)


def do_backup_diff():
    name = ask("backup name or substring")
    if name:
        tool("backup", "diff", name)


def do_placeholder(which: str):
    def fn():
        out.emit(f"  {which} is a design placeholder — its DESIGN_PROMPT.MD is a")
        out.emit("  stub awaiting the architect's interactive-editor pass. Not yet")
        out.emit("  implemented. Use 'Bond: replace weapon' for weapon swaps today.")
    return fn


# ---------------------------------------------------------------------------
# Menu definitions (structure mirrors the legacy menu)
# ---------------------------------------------------------------------------

def menu_backup():
    return [
        ("Make backup (light / heavy / both)", _run(do_backup_make)),
        ("Restore backup (interactive)",       _run(lambda: tool("backup", "restore"))),
        ("List backups",                       _run(lambda: tool("backup", "list"))),
        ("Back",                               None),
    ]


def menu_game_files():
    return [
        ("Unpack bundle      (-> world/_workdir)", _run(lambda: tool("extractor", "unpack"))),
        ("Decrypt            (_workdir -> world/json)", _run(lambda: tool("extractor", "decrypt"))),
        ("Encrypt            (world/json -> _workdir)", _run(lambda: tool("extractor", "encrypt"))),
        ("Pack               (_workdir -> bundle)", _run(lambda: tool("extractor", "pack"))),
        ("Back",                                    None),
    ]


def menu_database():
    return [
        ("Import   (JSON -> db)",                 _run(lambda: tool("import", "json"))),
        ("Export   (db -> JSON, in-place)",       _run(lambda: tool("export", "run", "--in-place"))),
        ("Export   (db -> JSON, to world/json_out)",
         _run(lambda: tool("export", "run", "--out", str(paths.WORLD_DIR / "json_out")))),
        ("Link     (rebuild all link_info)",      _run(lambda: tool("link", "init"))),
        ("Lookup   (walk an entity's relations)", _run(do_walk)),
        ("Show     (one entity's link_info)",     _run(do_show)),
        ("Back",                                  None),
    ]


def menu_ammo():
    return [
        ("Research -> real_world (parse research/*.md)", _run(lambda: tool("research", "run"))),
        ("Scale ranges (real_world -> current + min_range)", _run(lambda: tool("scale", "run"))),
        ("Back",                                          None),
    ]


def menu_mutations():
    return [
        ("Editor (guided unit edit: specs/price/armor/weapons/mods/abilities)",
         _run(lambda: tool("editor"))),
        ("Bond: replace weapon on a unit", _run(do_bond_replace)),
        ("Back",                           None),
    ]


def menu_diagnostics():
    return [
        ("Diff two JSON dirs/files",            _run(do_diff)),
        ("Check patch (live json vs backup)",   _run(lambda: tool("check_patch", "run"))),
        ("Backup diff (snapshot vs live json)", _run(do_backup_diff)),
        ("Back",                                None),
    ]


def root_menu():
    return [
        ("Backup ...",                          menu_backup),
        ("Game files ...",                      menu_game_files),
        ("Database  (import / export / link) ...", menu_database),
        ("Ammunition  (research / scale) ...",  menu_ammo),
        ("Mutations  (bond / editors) ...",     menu_mutations),
        ("Diagnostics  (diff / check_patch) ...", menu_diagnostics),
        ("Import pipeline  (clean -> unpack -> decrypt -> import -> link init)",
         _run(lambda: pipeline("import_pipeline", "run"))),
        ("Export pipeline  (backup? -> export -> diff -> encrypt -> pack)",
         _run(lambda: pipeline("export_pipeline", "run"))),
        ("Quit",                                None),
    ]


# ---------------------------------------------------------------------------
# Menu loop (ported verbatim from the legacy menu)
# ---------------------------------------------------------------------------

def render_menu(title, breadcrumb, items, selected):
    header(title, breadcrumb)
    for i, (label, _) in enumerate(items):
        marker = '>' if (ARROW_KEYS and i == selected) else ' '
        print(f"  {marker} {i+1:>2}) {label}")
    print()
    if ARROW_KEYS:
        print("  [arrows] move   [enter] select   [esc] back")
    else:
        print("  enter number, or 'b'/'q' for back")


def run_menu(title, breadcrumb, items_fn, is_root=False):
    selected = 0
    while True:
        items = items_fn()
        if selected >= len(items):
            selected = 0
        render_menu(title, breadcrumb, items, selected)

        if ARROW_KEYS:
            try:
                key = _msvcrt_getch()
            except KeyboardInterrupt:
                return
            if key == 'up':
                selected = (selected - 1) % len(items); continue
            if key == 'down':
                selected = (selected + 1) % len(items); continue
            if key == 'esc':
                if is_root:
                    continue
                return
            if key == 'enter':
                idx = selected
            elif key in ('q',) and is_root:
                return
            elif key in ('b',) and not is_root:
                return
            elif key.isdigit():
                idx = int(key) - 1
                if idx < 0 or idx >= len(items):
                    continue
            else:
                continue
        else:
            try:
                raw = input("  pick: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return
            if not raw:
                continue
            if raw in ('q',) and is_root:
                return
            if raw in ('b',) and not is_root:
                return
            if not raw.isdigit():
                continue
            idx = int(raw) - 1
            if idx < 0 or idx >= len(items):
                continue

        label, action = items[idx]
        if action is None:
            return
        if callable(action):
            result = action()
            if isinstance(result, list) or (action in (menu_backup, menu_game_files,
                    menu_database, menu_ammo, menu_mutations, menu_diagnostics)):
                run_menu('', f"{breadcrumb} > {label}" if breadcrumb else label,
                         action, is_root=False)


def _placement_warning():
    ok, _bundle, _reason = placement.check_placement()
    if ok:
        return
    clear()
    for line in placement.warning_lines():
        print(line)
    try:
        input("\n  [enter to continue to the menu] ")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv=None):
    _placement_warning()
    run_menu('', '', root_menu, is_root=True)


if __name__ == '__main__':
    main()
