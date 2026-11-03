"""Injected formulas.

A formula file is named for the method it hooks. `change` says whether the
new code runs after the game method, before it, inside it, or instead of it.
This build only accepts the one forest-cover postfix.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.errors import PipelineError

METHOD = "BrokenArrow.Client.Ecs.BattleSystem.BattleSystemHelpers.CalculateHitDamage"
FORMULA = "damage * (1 - reduction * (1 - clamp(IgnoreCover, 0, 1)))"
RELATIVE = Path("BattleSystemHelpers") / "CalculateHitDamage.json"
REQUIRED = ["InfantryUnitComponent", "TerrainTypeComponent"]
KEYS = {
    "method",
    "change",
    "requires",
    "terrain",
    "formula",
    "reduction",
    "damage",
    "IgnoreCover",
}


def formulas_in(directory: Path) -> list[Path]:
    """Every formula file under a channel directory."""
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def validate_formula(path: Path) -> dict:
    """Raise PipelineError unless this is the forest-cover postfix."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PipelineError(f"{path} must be a JSON object")
    extra = set(loaded) - KEYS
    missing = KEYS - set(loaded)
    if extra or missing:
        raise PipelineError(f"{path} keys must be {sorted(KEYS)}")
    if loaded["method"] != METHOD:
        raise PipelineError(f"{path} method is not {METHOD}")
    if loaded["change"] != "after":
        raise PipelineError(f"{path} change {loaded['change']!r} is not implemented")
    if loaded["requires"] != REQUIRED:
        raise PipelineError(f"{path} requires {REQUIRED}")
    if loaded["terrain"] != "TerrainType.Forest":
        raise PipelineError(f"{path} terrain must be TerrainType.Forest")
    if loaded["formula"] != FORMULA:
        raise PipelineError(f"{path} formula is not the forest cover postfix")
    reduction = loaded["reduction"]
    if isinstance(reduction, bool) or not isinstance(reduction, (int, float)) or not 0 <= reduction <= 1:
        raise PipelineError(f"{path} reduction must be a number from 0 to 1")
    if loaded["damage"] != "return":
        raise PipelineError(f"{path} damage must be the method return value")
    if loaded["IgnoreCover"] != "Ammunitions.IgnoreCover":
        raise PipelineError(f"{path} IgnoreCover must be Ammunitions.IgnoreCover")
    relative = path.as_posix()
    if not relative.endswith(RELATIVE.as_posix()):
        raise PipelineError(f"{path} must live at formulas/{RELATIVE.as_posix()}")
    return loaded
