"""On-disk vanilla snapshots and the patched object for one build."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import Config
from pipeline.errors import PipelineError
from pipeline.tables import FIELD_ORDER, FIELD_TO_FILE


def vanilla_dir(cfg: Config, build_id: str) -> Path:
    return cfg.cache_dir / "vanilla" / build_id


def patched_blob_path(cfg: Config, build_id: str, channel: str = "stable") -> Path:
    return cfg.cache_dir / "build" / build_id / channel / "object.bin"


def read_manifest(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"cannot read {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PipelineError(f"{path} must be a JSON object")
    build_id = loaded.get("build_id")
    if build_id is None:
        return None
    if not isinstance(build_id, str) or not build_id:
        raise PipelineError(f"{path} build_id must be a string or null")
    return build_id


def write_manifest(path: Path, build_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"build_id": build_id}, indent=2) + "\n"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_table(directory: Path, field: str):
    path = directory / f"{field}.json"
    if not path.is_file():
        raise PipelineError(f"missing {path}. Run decrypt for this build first.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"cannot read {path}: {exc}") from exc


def table_filename(field: str) -> str:
    return FIELD_TO_FILE[field]


def iter_fields():
    return FIELD_ORDER
