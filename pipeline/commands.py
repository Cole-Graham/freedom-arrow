"""Pipeline commands: discover, decrypt, survey, il2cpp, apply, inject, rebase, update, hangar."""

from __future__ import annotations

import gc
import json
from pathlib import Path

from pipeline.apply import build_object
from pipeline.bundle import find_database, identify_bundle
from pipeline.bundle_stream import extract_file, load_bytes, read_index, scan_assets, write_bundle
from pipeline.channels import STABLE, channel_bundle, channel_record_path, constants_dir, manifest_path, parse_channel
from pipeline.config import Config, require_bundle
from pipeline.constants import load_constants
from pipeline.crypto import aes_decrypt
from pipeline.database import parse_database
from pipeline.errors import PipelineError
from pipeline.hangar import run_hangar
from pipeline.rebase import rebase
from pipeline.il2cpp import write_il2cpp
from pipeline.snapshot import (
    load_table,
    patched_blob_path,
    read_manifest,
    vanilla_dir,
    write_json,
    write_manifest,
)
from pipeline.survey import write_survey
from pipeline.tables import FIELD_ORDER, FIELD_TO_FILE, OBJECT_NAME


def discover(cfg: Config) -> str:
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    assets_file, found = locate_database(bundle)
    directory = vanilla_dir(cfg, identity.build_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "object.bin").write_bytes(found.raw)
    write_json(directory / "discover.json", _discover_record(identity, found, assets_file))
    _print_found(identity.build_id, found, assets_file)
    print(f"wrote {directory / 'discover.json'}", flush=True)
    return identity.build_id


def survey(cfg: Config) -> Path:
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    assets_file, found = locate_database(bundle)
    return write_survey(cfg, identity, bundle, assets_file, found)


def il2cpp(cfg: Config) -> Path:
    return write_il2cpp(cfg)


def decrypt(cfg: Config) -> str:
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    directory = vanilla_dir(cfg, identity.build_id)
    if _snapshot_complete(directory):
        print(f"snapshot {identity.build_id} already exists", flush=True)
        return identity.build_id

    assets_file, found = locate_database(bundle)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "object.bin").write_bytes(found.raw)
    write_json(directory / "discover.json", _discover_record(identity, found, assets_file))
    _print_found(identity.build_id, found, assets_file)

    for field in FIELD_ORDER:
        ciphertext = found.blob.fields[field]
        (directory / f"{field}.b64").write_text(ciphertext, encoding="ascii")
        try:
            plaintext = aes_decrypt(ciphertext)
            value = json.loads(plaintext)
        except Exception as exc:
            raise PipelineError(f"{field} did not decrypt to JSON: {exc}") from exc
        write_json(directory / f"{field}.json", value)
        rows = len(value) if isinstance(value, list) else 1
        print(f"  {field:<36} rows={rows}", flush=True)

    print(f"wrote {directory}", flush=True)
    return identity.build_id


def apply(cfg: Config, channel: str = STABLE) -> Path:
    channel = parse_channel(channel)
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    directory = vanilla_dir(cfg, identity.build_id)
    if not _snapshot_complete(directory):
        raise PipelineError(f"no snapshot for {identity.build_id}. Run decrypt first.")

    overrides = load_constants(constants_dir(cfg, channel))
    rebuilt, dirty = build_object(directory, overrides)
    original = (directory / "object.bin").read_bytes()
    if not dirty and rebuilt != original:
        raise PipelineError("empty constants changed the MonoBehaviour bytes")

    destination = patched_blob_path(cfg, identity.build_id, channel)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(rebuilt)
    if dirty:
        print(f"re-encrypted {', '.join(dirty)}", flush=True)
    else:
        print("no constants changed; object bytes match the vanilla snapshot", flush=True)
    print(f"wrote {destination}", flush=True)
    return destination


def inject(cfg: Config, channel: str = STABLE) -> Path:
    channel = parse_channel(channel)
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    directory = vanilla_dir(cfg, identity.build_id)
    expected_path = patched_blob_path(cfg, identity.build_id, channel)
    if not expected_path.is_file():
        raise PipelineError(f"missing {expected_path}. Run apply --channel {channel} first.")
    expected = expected_path.read_bytes()
    original = (directory / "object.bin").read_bytes()
    record = json.loads((directory / "discover.json").read_text(encoding="utf-8"))
    assets_file = record["assets_file"]

    index = read_index(bundle)
    print(f"extracting {assets_file}", flush=True)
    assets = extract_file(index, assets_file)
    env = load_bytes(assets)
    found = find_database(env)
    if found.raw != original:
        raise PipelineError("the bundle no longer matches the vanilla snapshot. Run decrypt again.")
    found.obj.set_raw_data(expected)
    serialized = next(iter(env.files.values())).save()
    del env
    del found
    del assets
    gc.collect()

    produced = channel_bundle(cfg, channel)
    print(f"repacking {channel} bundle to {produced}", flush=True)
    write_bundle(index, produced, {assets_file: serialized})
    del serialized
    gc.collect()

    print(f"reloading {assets_file} from {produced}", flush=True)
    saved_assets = extract_file(read_index(produced), assets_file)
    saved = find_database(load_bytes(saved_assets))
    confirm_saved(saved.raw, expected, directory, cfg, channel)
    produced_id = identify_bundle(produced, cfg.cache_dir)
    write_json(
        channel_record_path(cfg, channel),
        {
            "channel": channel,
            "build_id": identity.build_id,
            "sha256": produced_id.sha256,
        },
    )
    print(f"injected {produced}", flush=True)
    return produced


def rebase_command(cfg: Config, accept: bool, channel: str = STABLE) -> None:
    channel = parse_channel(channel)
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    decrypt(cfg)
    channel_manifest = manifest_path(cfg, channel)
    old_id = read_manifest(channel_manifest)
    if old_id is None:
        raise PipelineError(f"{channel} manifest has no build_id yet. Run update --channel {channel} to pin this build.")
    if old_id == identity.build_id:
        print(f"{channel} manifest already matches {identity.build_id}", flush=True)
        return
    rebase(
        old_dir=vanilla_dir(cfg, old_id),
        new_dir=vanilla_dir(cfg, identity.build_id),
        constants_dir=constants_dir(cfg, channel),
        manifest_path=channel_manifest,
        new_build_id=identity.build_id,
        report_path=cfg.cache_dir / f"rebase-conflicts-{channel}.json",
        accept=accept,
    )


def update(cfg: Config, accept: bool, channel: str = STABLE) -> None:
    channel = parse_channel(channel)
    bundle = require_bundle(cfg)
    identity = identify_bundle(bundle, cfg.cache_dir)
    decrypt(cfg)
    channel_manifest = manifest_path(cfg, channel)
    old_id = read_manifest(channel_manifest)
    if old_id is None:
        write_manifest(channel_manifest, identity.build_id)
        print(f"pinned {channel} manifest to {identity.build_id}", flush=True)
    elif old_id != identity.build_id:
        rebase(
            old_dir=vanilla_dir(cfg, old_id),
            new_dir=vanilla_dir(cfg, identity.build_id),
            constants_dir=constants_dir(cfg, channel),
            manifest_path=channel_manifest,
            new_build_id=identity.build_id,
            report_path=cfg.cache_dir / f"rebase-conflicts-{channel}.json",
            accept=accept,
        )
    apply(cfg, channel)
    inject(cfg, channel)


def hangar(cfg: Config) -> int:
    return run_hangar(cfg)


def confirm_saved(saved_raw: bytes, expected: bytes, vanilla: Path, cfg: Config, channel: str = STABLE) -> None:
    """The saved object must carry the patched ciphertext and the same other fields."""
    if saved_raw != expected:
        saved_blob = parse_database(saved_raw)
        expected_blob = parse_database(expected)
        if saved_blob.fields != expected_blob.fields:
            raise PipelineError("saved bundle decrypted to different fields than the patched object")
        print("saved object fields match the patched object", flush=True)
    else:
        print("saved object bytes match the patched object", flush=True)

    overrides = load_constants(constants_dir(cfg, channel))
    parsed = parse_database(saved_raw)
    for field in FIELD_ORDER:
        table_overrides = overrides.get(field) or {}
        original_b64 = (vanilla / f"{field}.b64").read_text(encoding="ascii")
        if not table_overrides:
            if parsed.fields[field] != original_b64:
                raise PipelineError(f"{field} changed without a constant")
            continue
        rows = json.loads(aes_decrypt(parsed.fields[field]))
        vanilla_rows = load_table(vanilla, field)
        _confirm_table(FIELD_TO_FILE[field], vanilla_rows, rows, table_overrides)


def _confirm_table(table_name: str, vanilla_rows, patched_rows, overrides: dict[str, dict]) -> None:
    if not isinstance(patched_rows, list) or not isinstance(vanilla_rows, list):
        raise PipelineError(f"{table_name} confirmation expected row lists")
    vanilla_index = {str(row["Id"]): row for row in vanilla_rows if isinstance(row, dict) and "Id" in row}
    patched_index = {str(row["Id"]): row for row in patched_rows if isinstance(row, dict) and "Id" in row}
    for row_id, fields in overrides.items():
        patched = patched_index[row_id]
        original = vanilla_index[row_id]
        for column, value in fields.items():
            if patched[column] != value:
                raise PipelineError(
                    f"{table_name} Id {row_id} {column} is {patched[column]!r}, expected {value!r}"
                )
            print(f"confirmed {table_name} Id {row_id} {column}={value!r}", flush=True)
        for column, value in original.items():
            if column in fields:
                continue
            if patched.get(column) != value:
                raise PipelineError(f"{table_name} Id {row_id} field {column} changed without a constant")
    for row_id, original in vanilla_index.items():
        if row_id in overrides:
            continue
        if patched_index.get(row_id) != original:
            raise PipelineError(f"{table_name} Id {row_id} changed without a constant")


def _snapshot_complete(directory: Path) -> bool:
    if not (directory / "object.bin").is_file() or not (directory / "discover.json").is_file():
        return False
    return all(
        (directory / f"{field}.json").is_file() and (directory / f"{field}.b64").is_file()
        for field in FIELD_ORDER
    )


def locate_database(bundle: Path):
    """Return (assets file name, FoundObject).

    globalgamemanagers and resources are checked first, because those are the
    only files large enough to hold the database and they can be extracted
    without decompressing the rest of the archive.
    """
    index = read_index(bundle)
    preferred = [
        entry.name
        for entry in index.files
        if entry.name in ("globalgamemanagers.assets", "resources.assets")
    ]
    for name in preferred:
        found = _database_in_assets(index, name)
        if found is not None:
            return name, found

    located: dict = {}

    def on_file(name: str, data: bytes) -> bool:
        if name in preferred or b"DataBaseCompiled" not in data:
            return False
        parsed = _parse_assets(name, data)
        if parsed is None:
            return False
        located["assets"] = name
        located["object"] = parsed
        return True

    print(f"scanning remaining assets in {bundle.name}", flush=True)
    scan_assets(index, on_file)
    if "object" not in located:
        names = [entry.name for entry in index.files if entry.name.endswith(".assets")]
        raise PipelineError(
            f"{OBJECT_NAME} was not found in {bundle}.\nAssets files:\n  " + "\n  ".join(names)
        )
    return located["assets"], located["object"]


def _database_in_assets(index, name: str):
    print(f"extracting {name}", flush=True)
    return _parse_assets(name, extract_file(index, name))


def _parse_assets(name: str, data: bytes):
    if b"DataBaseCompiled" not in data:
        print(f"  {name}: name not present", flush=True)
        return None
    print(f"  parsing {name}", flush=True)
    try:
        return find_database(load_bytes(data))
    except PipelineError as exc:
        print(f"  {name} is not the database: {exc}", flush=True)
        return None


def _discover_record(identity, found, assets_file: str) -> dict:
    script = found.blob.script or (None, None)
    game_object = found.blob.game_object or (None, None)
    return {
        "build_id": identity.build_id,
        "unity_version": identity.unity_version,
        "bundle_sha256": identity.sha256,
        "path_id": found.path_id,
        "script_file_id": script[0],
        "script_path_id": script[1],
        "game_object_file_id": game_object[0],
        "game_object_path_id": game_object[1],
        "raw_size": len(found.raw),
        "typetree": found.typetree,
        "m_name": OBJECT_NAME,
        "level": found.blob.level,
        "enabled": found.blob.enabled,
        "assets_file": assets_file,
        "candidates": [
            {"path_id": path_id, "units": count} for path_id, count in found.candidates
        ],
    }


def _print_found(build_id: str, found, assets_file: str) -> None:
    script = found.blob.script
    counts = ", ".join(f"{path_id}:{count}" for path_id, count in found.candidates) or "n/a"
    print(
        f"build {build_id}  {OBJECT_NAME} file={assets_file} path_id={found.path_id} "
        f"bytes={len(found.raw)} typetree={found.typetree} script={script} candidates=[{counts}]",
        flush=True,
    )
