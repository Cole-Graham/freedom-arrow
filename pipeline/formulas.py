"""Injected formulas.

A formula file names the game method a hook runs at. `change` says whether
the new code runs after the game method, before it, inside it, or instead
of it. Only `after` is implemented. `parameters` holds the values that hook
reads. This module checks that envelope for every file. It does not know
which hooks exist.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.errors import PipelineError

KEYS = {"method", "change", "parameters"}
CHANGES = ("after", "before", "inside", "instead")
IMPLEMENTED = frozenset({"after"})


def formulas_in(directory: Path) -> list[Path]:
    """Every formula file under a channel directory."""
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def validate_formula(path: Path, directory: Path) -> dict:
    """Raise PipelineError unless this file is a formula envelope."""
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
    method = loaded["method"]
    if not isinstance(method, str) or not method.strip():
        raise PipelineError(f"{path} method must be a non-empty string")
    _check_change(path, loaded["change"])
    _check_parameters(path, loaded["parameters"])
    _check_path(path, directory, method)
    return loaded


def _check_change(path: Path, change: object) -> None:
    if not isinstance(change, str) or change not in CHANGES:
        raise PipelineError(f"{path} change must be one of: {', '.join(CHANGES)}")
    if change not in IMPLEMENTED:
        raise PipelineError(f"{path} change {change!r} is not implemented")


def _check_parameters(path: Path, parameters: object) -> None:
    if not isinstance(parameters, dict):
        raise PipelineError(f"{path} parameters must be an object")
    for name, value in parameters.items():
        if _parameter_value(value):
            continue
        raise PipelineError(
            f"{path} parameter {name} must be a number, string, boolean, or array of those"
        )


def _parameter_value(value: object) -> bool:
    if _scalar(value):
        return True
    return isinstance(value, list) and all(_scalar(item) for item in value)


def _scalar(value: object) -> bool:
    if isinstance(value, bool) or isinstance(value, str):
        return True
    return isinstance(value, (int, float))


def _check_path(path: Path, directory: Path, method: str) -> None:
    try:
        relative = path.relative_to(directory)
    except ValueError as exc:
        raise PipelineError(f"{path} is outside {directory}") from exc
    suffix = ".".join(relative.with_suffix("").parts)
    if suffix and (method == suffix or method.endswith("." + suffix)):
        return
    raise PipelineError(f"{path} path does not match method {method}")
