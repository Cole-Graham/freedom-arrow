"""Developer config.

config.template.YAML is committed. Each developer copies it to config.YAML,
which is gitignored and is the only file the pipeline reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from pipeline.errors import PipelineError

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_NAME = "config.template.YAML"
CONFIG_NAME = "config.YAML"


@dataclass(frozen=True)
class Config:
    repo_root: Path
    game_root: Path
    cache_dir: Path
    dist_dir: Path
    constants_dir: Path
    manifest_path: Path
    write_game_bundle: bool
    backup_dir: Path
    game_exe: Path | None
    launch_args: tuple[str, ...]

    @property
    def bundle_path(self) -> Path:
        return self.game_root / "BrokenArrow_Data" / "data.unity3d"

    @property
    def resolved_exe(self) -> Path:
        if self.game_exe is not None:
            return self.game_exe
        return self.game_root / "BrokenArrow.exe"


def load_config(path: Path | None = None) -> Config:
    repo_root = REPO_ROOT
    config_path = path if path is not None else repo_root / CONFIG_NAME
    if not config_path.is_file():
        raise PipelineError(
            f"missing {config_path.name}. Copy {TEMPLATE_NAME} to {CONFIG_NAME} and set game_root."
        )
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PipelineError(f"cannot read {config_path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PipelineError(f"{config_path.name} must be a mapping")

    game_root_text = _required_str(loaded, "game_root")
    if not game_root_text:
        raise PipelineError("set game_root in config.YAML to the Broken Arrow install directory")

    write_game = loaded.get("write_game_bundle", False)
    if not isinstance(write_game, bool):
        raise PipelineError("write_game_bundle must be true or false")

    launch_args = loaded.get("launch_args", [])
    if not isinstance(launch_args, list) or not all(isinstance(item, str) for item in launch_args):
        raise PipelineError("launch_args must be a list of strings")

    game_exe_text = loaded.get("game_exe", "") or ""
    if not isinstance(game_exe_text, str):
        raise PipelineError("game_exe must be a string")

    return Config(
        repo_root=repo_root,
        game_root=Path(game_root_text),
        cache_dir=_resolve(repo_root, loaded, "cache_dir", "cache"),
        dist_dir=_resolve(repo_root, loaded, "dist_dir", "dist"),
        constants_dir=_resolve(repo_root, loaded, "constants_dir", "mod/constants"),
        manifest_path=_resolve(repo_root, loaded, "manifest_path", "mod/manifest.json"),
        write_game_bundle=write_game,
        backup_dir=_resolve(repo_root, loaded, "backup_dir", "cache/backups"),
        game_exe=Path(game_exe_text) if game_exe_text else None,
        launch_args=tuple(launch_args),
    )


def require_bundle(cfg: Config) -> Path:
    bundle = cfg.bundle_path
    if not bundle.is_file():
        raise PipelineError(
            f"bundle not found at {bundle}. game_root must contain BrokenArrow_Data/data.unity3d"
        )
    return bundle


def _required_str(loaded: dict, key: str) -> str:
    if key not in loaded:
        raise PipelineError(f"config.YAML is missing {key}")
    value = loaded[key]
    if value is None:
        return ""
    if not isinstance(value, str):
        raise PipelineError(f"{key} must be a string")
    return value.strip()


def _resolve(repo_root: Path, loaded: dict, key: str, default: str) -> Path:
    raw = loaded.get(key, default)
    if not isinstance(raw, str) or not raw.strip():
        raise PipelineError(f"{key} must be a non-empty path")
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    return path
