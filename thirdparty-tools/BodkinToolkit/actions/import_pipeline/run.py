"""import_pipeline — clean -> unpack -> decrypt -> import -> link init.

Chains v3 tools to turn the game bundle into an editable db. Contains no
domain logic.
"""
from __future__ import annotations

import shutil
import sys

from ...core import out, paths, prompt, proc
from .._common import banner, step, run_step


def _wipe_workdir():
    wd = paths.WORK_DIR
    if wd.is_dir():
        for f in wd.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)
    else:
        wd.mkdir(parents=True, exist_ok=True)
    out.emit(f"  cleaned {wd}")


def _detect_and_wipe_json(yes: bool):
    jd = paths.JSON_DIR
    existing = sorted(jd.glob("*.json")) if jd.is_dir() else []
    if not existing:
        return
    out.emit(f"  found existing data in: {jd} ({len(existing)} files)")
    if not yes:
        try:
            prompt.confirm_destructive("Wipe json/ before import?", yes_flag=False)
        except prompt.Cancelled:
            out.emit("  keeping existing json/ (will be overwritten by decrypt)")
            return
    n = 0
    for f in existing:
        f.unlink()
        n += 1
    out.emit(f"  wiped {n} files from {jd}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # accept an optional leading 'run' verb plus --yes
    argv = [a for a in argv if a != "run"]
    yes = "--yes" in argv

    banner("Import pipeline")
    _wipe_workdir()
    _detect_and_wipe_json(yes)

    step("extractor unpack (bundle -> workdir/)")
    run_step("extractor", "unpack")

    step("extractor decrypt (workdir/ -> json/)")
    run_step("extractor", "decrypt")

    step("import json (json/ -> db)")
    run_step("import", "json", "--yes")

    step("link init (compute every link_info)")
    run_step("link", "init")

    out.emit("")
    out.emit("  Import pipeline complete.")


if __name__ == "__main__":
    main()
