"""Stable and Testing outputs.

Stable constants stay in the configured mod directory. Testing is a second
tree under mod/testing/ so a development bundle can be built without
replacing the stable one.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.config import Config
from pipeline.errors import PipelineError

STABLE = "stable"
TESTING = "testing"
CHANNELS = (STABLE, TESTING)


def parse_channel(name: str) -> str:
    if name not in CHANNELS:
        raise PipelineError(f"channel must be one of: {', '.join(CHANNELS)}")
    return name


def constants_dir(cfg: Config, channel: str) -> Path:
    channel = parse_channel(channel)
    if channel == STABLE:
        return cfg.constants_dir
    return cfg.repo_root / "mod" / "testing" / "constants"


def formulas_dir(cfg: Config, channel: str) -> Path:
    channel = parse_channel(channel)
    if channel == STABLE:
        return cfg.repo_root / "mod" / "formulas"
    return cfg.repo_root / "mod" / "testing" / "formulas"


def manifest_path(cfg: Config, channel: str) -> Path:
    channel = parse_channel(channel)
    if channel == STABLE:
        return cfg.manifest_path
    return cfg.repo_root / "mod" / "testing" / "manifest.json"


def channel_dir(cfg: Config, channel: str) -> Path:
    return cfg.dist_dir / parse_channel(channel)


def channel_bundle(cfg: Config, channel: str) -> Path:
    return channel_dir(cfg, channel) / "data.unity3d"


def channel_record_path(cfg: Config, channel: str) -> Path:
    return channel_dir(cfg, channel) / "channel.json"
