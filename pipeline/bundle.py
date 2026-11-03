"""Bundle identity and DataBaseCompiled lookup.

The object is selected by its name, never by a hardcoded PathID.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.crypto import aes_decrypt, has_marker
from pipeline.database import DatabaseBlob, parse_database
from pipeline.errors import PipelineError
from pipeline.tables import FIELD_ORDER, OBJECT_NAME


@dataclass(frozen=True)
class BuildIdentity:
    unity_version: str
    sha256: str
    build_id: str


@dataclass
class FoundObject:
    obj: object
    path_id: int
    raw: bytes
    blob: DatabaseBlob
    typetree: bool
    inspected: list[dict]
    candidates: list[tuple[int, int]] = field(default_factory=list)


def read_unity_version(bundle: Path) -> str:
    """Read the Unity engine version from a UnityFS header."""
    with bundle.open("rb") as handle:
        header = handle.read(256)
    if not header.startswith(b"UnityFS\x00"):
        raise PipelineError(f"{bundle} is not a UnityFS bundle")
    offset = len(b"UnityFS\x00")
    offset += 4  # format version, big-endian
    _player, offset = _cstring(header, offset)
    engine, _offset = _cstring(header, offset)
    if not engine:
        raise PipelineError(f"{bundle} header has no engine version")
    return engine


def identify_bundle(bundle: Path, cache_dir: Path) -> BuildIdentity:
    """Return the build id, reusing a size/mtime cache so the 7 GB hash runs once."""
    stat = bundle.stat()
    cache_dir.mkdir(parents=True, exist_ok=True)
    record_path = cache_dir / "bundle-ids.json"
    cache = _read_id_cache(record_path)
    key = str(bundle.resolve())
    record = cache.get(key)
    if (
        isinstance(record, dict)
        and record.get("size") == stat.st_size
        and record.get("mtime_ns") == stat.st_mtime_ns
        and record.get("build_id")
    ):
        return BuildIdentity(
            unity_version=record["unity_version"],
            sha256=record["sha256"],
            build_id=record["build_id"],
        )

    version = read_unity_version(bundle)
    digest = hashlib.sha256()
    with bundle.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    sha = digest.hexdigest()
    identity = BuildIdentity(unity_version=version, sha256=sha, build_id=f"{version}-{sha[:16]}")
    cache[key] = {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "unity_version": identity.unity_version,
        "sha256": identity.sha256,
        "build_id": identity.build_id,
    }
    record_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    return identity


def _read_id_cache(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(loaded, dict) and "build_id" not in loaded:
        return loaded
    return {}


def find_database(env) -> FoundObject:
    """Select the DataBaseCompiled MonoBehaviour by name."""
    inspected: list[dict] = []
    matches: list[FoundObject] = []
    mono = [obj for obj in env.objects if obj.type.name == "MonoBehaviour"]
    mono.sort(key=lambda obj: obj.byte_size, reverse=True)

    for obj in mono:
        has_tree = bool(getattr(obj, "serialized_type", None) and obj.serialized_type.nodes)
        peeked = _peek_name(obj) if has_tree else None
        entry = {
            "path_id": obj.path_id,
            "byte_size": obj.byte_size,
            "name": peeked,
            "typetree": has_tree,
        }
        if len(inspected) < 30:
            inspected.append(entry)

        if peeked not in (None, OBJECT_NAME) and has_tree:
            continue
        if peeked is None and obj.byte_size < 1024:
            continue

        raw = obj.get_raw_data()
        if OBJECT_NAME.encode("utf-8") not in raw and peeked != OBJECT_NAME:
            continue
        try:
            blob = parse_database(raw)
        except ValueError:
            continue
        if not all(has_marker(blob.fields[field]) for field in FIELD_ORDER):
            continue
        matches.append(
            FoundObject(
                obj=obj,
                path_id=obj.path_id,
                raw=raw,
                blob=blob,
                typetree=has_tree,
                inspected=inspected,
            )
        )

    if not matches:
        raise PipelineError(_not_found_message(inspected))
    chosen = _select_database(matches)
    chosen.candidates = [(item.path_id, _unit_count(item)) for item in matches]
    return chosen


def _select_database(matches: list[FoundObject]) -> FoundObject:
    """Prefer MainBuildDatabase with level 2.

    The bundle also carries mission snapshots. When no object exposes that
    flag, the roster with the most unit rows is the fallback, and every
    candidate path id and unit count is printed.
    """
    listed = ", ".join(
        f"{item.path_id}:{_unit_count(item)} main={item.blob.main_build_database} level={item.blob.level}"
        for item in matches
    )
    flagged = [
        item
        for item in matches
        if item.blob.main_build_database is True and item.blob.level == 2
    ]
    if flagged:
        chosen = max(flagged, key=lambda item: (_unit_count(item), len(item.raw)))
        print(f"main database path_id={chosen.path_id} candidates=[{listed}]", flush=True)
        return chosen
    print(f"no MainBuildDatabase level 2; using most units. candidates=[{listed}]", flush=True)
    return max(matches, key=lambda item: (_unit_count(item), len(item.raw)))


def _unit_count(found: FoundObject) -> int:
    try:
        rows = json.loads(aes_decrypt(found.blob.fields["Units"]))
    except Exception:
        return -1
    if isinstance(rows, list):
        return len(rows)
    return -1


def _peek_name(obj) -> str | None:
    try:
        name = obj.peek_name()
    except Exception:
        return None
    if isinstance(name, str):
        return name
    return None


def _not_found_message(inspected: list[dict]) -> str:
    lines = [f"{OBJECT_NAME} was not found. Inspected MonoBehaviours:"]
    if not inspected:
        lines.append("  (none)")
    for entry in inspected:
        lines.append(
            f"  path_id={entry['path_id']} bytes={entry['byte_size']} "
            f"name={entry['name']!r} typetree={entry['typetree']}"
        )
    return "\n".join(lines)


def _cstring(buf: bytes, offset: int) -> tuple[str, int]:
    end = buf.index(b"\x00", offset)
    return buf[offset:end].decode("ascii"), end + 1
