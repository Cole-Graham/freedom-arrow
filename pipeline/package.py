"""Build a .bamod modpack for BAModLauncher.

A .bamod is a zip. BAModManager installs paths under Mods, Plugins, UserData,
and UserLibs. The gameplay constants go in UserData/FreedomArrow/constants.
The patched data.unity3d stays in dist/ and is not packed: a GitHub release
asset cannot hold that archive, and the manager does not install
BrokenArrow_Data.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from pipeline.apply import validate_applied
from pipeline.bundle import identify_bundle
from pipeline.channels import channel_dir, constants_dir, formulas_dir, parse_channel
from pipeline.config import Config
from pipeline.constants import load_constants
from pipeline.errors import PipelineError
from pipeline.formulas import formulas_in, validate_formula
from pipeline.snapshot import vanilla_dir
from pipeline.tables import FIELD_TO_FILE

PLUGIN_DLL = Path("runtime") / "FreedomArrow" / "bin" / "Release" / "net6.0" / "FreedomArrow.dll"

MODPACK_PATH = Path("mod") / "modpack.json"
USERDATA_ROOT = "UserData/FreedomArrow"


def package(cfg: Config, channel: str) -> Path:
    channel = parse_channel(channel)
    meta = load_modpack(cfg.repo_root / MODPACK_PATH)
    repo = _repo_for(meta, channel)
    info = {
        "id": meta["id"],
        "name": meta["name"],
        "version": meta["version"],
        "type": "modpack",
    }
    for key in ("author", "description", "gameVersion", "website"):
        if meta.get(key):
            info[key] = meta[key]
    if repo:
        info["repo"] = repo
    else:
        print(
            f"warning: {channel} mod.json has no repo. "
            "BAModLauncher cannot check GitHub for updates until mod/modpack.json sets one.",
            flush=True,
        )

    _check_channel(cfg, channel)
    files = _constant_files(constants_dir(cfg, channel))
    files.extend(_formula_files(formulas_dir(cfg, channel)))
    plugin = _plugin_bytes(cfg.repo_root)
    build_id = _channel_build_id(channel_dir(cfg, channel) / "channel.json")
    readme = _readme(meta, channel, build_id, repo)

    destination = channel_dir(cfg, channel) / f"{_safe_name(meta['name'])}-{meta['version']}.bamod"
    destination.parent.mkdir(parents=True, exist_ok=True)
    _write_zip(destination, info, readme, files, plugin, channel, build_id)
    _write_launcher_json(cfg, meta)
    print(f"wrote {destination} ({len(files)} constant file(s))", flush=True)
    return destination


def load_modpack(path: Path) -> dict:
    if not path.is_file():
        raise PipelineError(f"missing {path}. It needs id, name, and version.")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"cannot read {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PipelineError(f"{path} must be a JSON object")
    for key in ("id", "name", "version"):
        value = loaded.get(key)
        if not isinstance(value, str) or not value.strip():
            raise PipelineError(f"{path} is missing {key}")
        loaded[key] = value.strip()
    if loaded["id"] != loaded["id"].lower():
        raise PipelineError(f"{path} id must be lower-case")
    return loaded


def _repo_for(meta: dict, channel: str) -> str:
    if channel == "testing" and isinstance(meta.get("testingRepo"), str) and meta["testingRepo"].strip():
        return meta["testingRepo"].strip()
    repo = meta.get("repo")
    return repo.strip() if isinstance(repo, str) else ""


def _constant_files(directory: Path) -> list[tuple[str, bytes]]:
    packed: list[tuple[str, bytes]] = []
    if not directory.is_dir():
        return packed
    known = set(FIELD_TO_FILE.values())
    for path in sorted(directory.glob("*.json")):
        if path.name not in known:
            raise PipelineError(f"unknown constants file {path.name}")
        text = path.read_text(encoding="utf-8")
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PipelineError(f"{path.name} is not valid JSON: {exc}") from exc
        if value in ({}, []):
            continue
        packed.append((f"{USERDATA_ROOT}/constants/{path.name}", text.encode("utf-8")))
    return packed


def _formula_files(directory: Path) -> list[tuple[str, bytes]]:
    packed: list[tuple[str, bytes]] = []
    for path in formulas_in(directory):
        validate_formula(path)
        relative = path.relative_to(directory).as_posix()
        packed.append((f"{USERDATA_ROOT}/formulas/{relative}", path.read_bytes()))
    return packed


def _plugin_bytes(repo: Path) -> bytes:
    path = repo / PLUGIN_DLL
    if not path.is_file():
        raise PipelineError(
            f"missing {path}. Build it with: dotnet build runtime/FreedomArrow/FreedomArrow.csproj -c Release"
        )
    return path.read_bytes()


def _check_channel(cfg: Config, channel: str) -> None:
    for path in formulas_in(formulas_dir(cfg, channel)):
        validate_formula(path)
    bundle = cfg.bundle_path
    if not bundle.is_file():
        return
    identity = identify_bundle(bundle, cfg.cache_dir)
    directory = vanilla_dir(cfg, identity.build_id)
    if not (directory / "object.bin").is_file():
        raise PipelineError(f"no snapshot for {identity.build_id}. Run decrypt before package.")
    from pipeline.tables import FIELD_ORDER

    if not all((directory / f"{field}.json").is_file() for field in FIELD_ORDER):
        raise PipelineError(f"no snapshot for {identity.build_id}. Run decrypt before package.")
    validate_applied(directory, load_constants(constants_dir(cfg, channel)))


def _channel_build_id(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    build_id = loaded.get("build_id") if isinstance(loaded, dict) else None
    return build_id if isinstance(build_id, str) and build_id else None


def _readme(meta: dict, channel: str, build_id: str | None, repo: str) -> str:
    built = f" for game build `{build_id}`" if build_id else ""
    repo_line = f"Updates come from `{repo}`." if repo else "This build has no GitHub repo set, so the launcher will not auto-update it."
    return (
        f"# {meta['name']}\n\n"
        f"{meta.get('description') or 'Gameplay changes for Broken Arrow.'}\n\n"
        f"Channel: **{channel}**{built}. {repo_line}\n\n"
        "Install with BAModLauncher or BAModManager. PLAY starts Broken Arrow with "
        "Anti-Cheat disabled. **Play vanilla with no mods** removes MelonLoader's "
        "`version.dll` and starts the normal game.\n\n"
        "The gameplay constants in this package are under `UserData/FreedomArrow/constants/`. "
        "Injected formulas are under `UserData/FreedomArrow/formulas/`. "
        "`Mods/FreedomArrow.dll` applies both when the game loads its database. "
        "Do not play ranked or quick match while MelonLoader is installed.\n"
    )


def _write_zip(
    destination: Path,
    info: dict,
    readme: str,
    files: list[tuple[str, bytes]],
    plugin: bytes,
    channel: str,
    build_id: str | None,
) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mod.json", json.dumps(info, indent=2) + "\n")
        archive.writestr("README.md", readme)
        archive.writestr("Mods/FreedomArrow.dll", plugin)
        marker = {"channel": channel}
        if build_id:
            marker["build_id"] = build_id
        archive.writestr(f"{USERDATA_ROOT}/channel.json", json.dumps(marker, indent=2) + "\n")
        for name, payload in files:
            archive.writestr(name, payload)
    temporary.replace(destination)


def _write_launcher_json(cfg: Config, meta: dict) -> None:
    repo = meta.get("repo") if isinstance(meta.get("repo"), str) else ""
    testing = meta.get("testingRepo") if isinstance(meta.get("testingRepo"), str) else ""
    repo = repo.strip()
    testing = testing.strip()
    if not repo and not testing:
        return
    payload: dict[str, str] = {}
    if repo:
        payload["modpack"] = repo
    if testing:
        payload["testing"] = testing
    path = cfg.dist_dir / "launcher.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}", flush=True)


def _safe_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "" for ch in name)
    return cleaned or "FreedomArrow"
