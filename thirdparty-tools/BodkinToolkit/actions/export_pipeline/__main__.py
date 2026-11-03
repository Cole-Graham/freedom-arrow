"""export_pipeline — optional heavy backup -> export in-place -> diff ->
confirm -> encrypt -> pack.

Chains v3 tools to turn the editable db back into a patched game bundle.
Contains no domain logic.
"""
from __future__ import annotations

import sys

from ...core import out, paths, prompt, proc
from .._common import banner, step, run_step


def _latest_export_backup():
    base = paths.BACKUPS_DIR / "light"
    if not base.is_dir():
        return None
    snaps = [d for d in base.iterdir() if d.is_dir() and d.name.endswith("_export")]
    if not snaps:
        return None
    return max(snaps, key=lambda d: d.stat().st_mtime)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    argv = [a for a in argv if a != "run"]
    yes = "--yes" in argv
    no_backup = "--no-backup" in argv

    banner("Export pipeline")

    if not no_backup:
        take = yes is False and prompt.confirm(
            "Take heavy backup before patching?", default=False)
        if take:
            step("backup make heavy")
            run_step("backup", "make", "heavy", "--yes")

    step("export run --in-place (db -> json/)")
    run_step("export", "run", "--in-place", "--yes")

    snap = _latest_export_backup()
    if snap is not None:
        step("backup diff (verify changes)")
        r = proc.run_tool("diff", "run", "--left", str(snap),
                          "--right", str(paths.JSON_DIR), check=False, capture=True)
        out.emit(r.stdout.rstrip("\n") if r.stdout else "(no diff output)")
        if r.returncode == 0:
            out.emit("WARN: live json/ matches its pre-export snapshot. "
                     "Nothing will change in the game.")
            if not yes:
                prompt.confirm_destructive("Proceed anyway?", yes_flag=False)
        elif not yes:
            if not prompt.confirm("Changes look intentional?", default=True):
                out.error("ERR aborted by user after diff review", exit_code=1)

    step("extractor encrypt (json/ -> workdir/)")
    run_step("extractor", "encrypt")

    step("extractor pack (workdir/ -> bundle)")
    run_step("extractor", "pack", *(["--yes"] if yes else []))

    out.emit("")
    out.emit("  Export pipeline complete.")


if __name__ == "__main__":
    main()
