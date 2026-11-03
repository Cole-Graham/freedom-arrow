"""Swap the injected bundle in front of the game, launch, then restore.

This is the only command that writes inside game_root, and only when
write_game_bundle is true.
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone

from pipeline.config import Config, require_bundle
from pipeline.errors import PipelineError


def run_hangar(cfg: Config) -> int:
    if not cfg.write_game_bundle:
        raise PipelineError("hangar check requires write_game_bundle: true in config.YAML")

    bundle = require_bundle(cfg)
    injected = cfg.dist_dir / "stable" / "data.unity3d"
    if not injected.is_file():
        raise PipelineError(f"no stable bundle at {injected}. Run inject --channel stable first.")

    exe = cfg.resolved_exe
    if not exe.is_file():
        raise PipelineError(f"game executable not found at {exe}")

    cfg.backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = cfg.backup_dir / f"data.unity3d.{stamp}"
    print(f"backing up {bundle} -> {backup}", flush=True)
    shutil.copy2(bundle, backup)
    try:
        print(f"installing {injected}", flush=True)
        shutil.copy2(injected, bundle)
        command = [str(exe), *cfg.launch_args]
        print(f"launching {' '.join(command)}", flush=True)
        completed = subprocess.run(command, check=False)
        print(f"game exited {completed.returncode}", flush=True)
        return completed.returncode
    finally:
        print(f"restoring {backup}", flush=True)
        shutil.copy2(backup, bundle)
