"""Catalog terrain, cover, forest, and suppression data.

The 24 DataBaseCompiled tables are indexed in memory. Other MonoBehaviour
and TextAsset objects are kept when their name, a field, or a same-key AES
JSON blob matches those systems. Output stays under cache/survey/.
"""

from __future__ import annotations

import gc
import json
import re
import struct
from pathlib import Path

from pipeline.bundle import FoundObject
from pipeline.bundle_stream import load_bytes, read_index, scan_assets
from pipeline.config import Config
from pipeline.crypto import aes_decrypt, has_marker
from pipeline.errors import PipelineError
from pipeline.snapshot import load_table, vanilla_dir, write_json
from pipeline.tables import FIELD_ORDER, FIELD_TO_FILE, OBJECT_NAME

# Longer words match as substrings. Short words match a whole token so
# "buffer" and "close" do not count as buff / line of sight.
_WORDS: tuple[str, ...] = (
    "cover",
    "stealth",
    "optics",
    "forest",
    "building",
    "fog",
    "conceal",
    "suppress",
    "stress",
    "terrain",
)
_TOKEN_WORDS = frozenset({"los", "fow", "fowl"})
_SMALL_OBJECT = 64 * 1024
_SMALL_JSON = 64 * 1024
_MAX_STRING = 2_000_000
_MAX_PLAINTEXT = 20
_MAX_EXAMPLES = 5
_MAX_DISTINCT = 16


def interesting(text: str) -> bool:
    """True when a name or key looks like cover, forest, stealth, or suppression."""
    compact = "".join(ch for ch in text.lower() if ch.isalnum())
    if "lineofsight" in compact:
        return True
    if any(word in compact for word in _WORDS):
        return True
    if "buff" in compact and "buffer" not in compact:
        return True
    return any(token in _TOKEN_WORDS for token in _tokens(text))


def index_tables(tables: dict) -> list[dict]:
    """Key index for decrypted tables, with stats for cover-related columns."""
    fields = [field for field in FIELD_ORDER if field in tables]
    fields.extend(key for key in tables if key not in FIELD_ORDER)
    return [_index_table(field, tables[field]) for field in fields]


def catalog_monobehaviour(
    raw: bytes,
    typetree: dict | None = None,
    *,
    byte_size: int | None = None,
    typetree_present: bool | None = None,
) -> dict | None:
    """Describe one MonoBehaviour, or return None when nothing relevant is in it.

    DataBaseCompiled is omitted. Its tables are indexed separately.
    """
    header = _parse_header(raw)
    if header is not None and header[0] == OBJECT_NAME:
        return None
    name = header[0] if header is not None else None
    script = header[1] if header is not None else None
    return _assemble(
        name=name,
        script=script,
        strings=_iter_unity_strings(raw),
        byte_size=len(raw) if byte_size is None else byte_size,
        typetree=typetree,
        typetree_present=typetree is not None if typetree_present is None else typetree_present,
    )


def catalog_text_asset(
    raw: bytes,
    typetree: dict | None = None,
    *,
    byte_size: int | None = None,
    typetree_present: bool | None = None,
) -> dict | None:
    """Describe one TextAsset whose name or body matches, or return None."""
    name = _text_asset_name(raw)
    return _assemble(
        name=name,
        script=None,
        strings=_iter_unity_strings(raw),
        byte_size=len(raw) if byte_size is None else byte_size,
        typetree=typetree,
        typetree_present=typetree is not None if typetree_present is None else typetree_present,
    )


def write_survey(cfg: Config, identity, bundle: Path, assets_file: str, found: FoundObject) -> Path:
    """Read the bundle and write cache/survey/<build-id>/report.json."""
    directory = vanilla_dir(cfg, identity.build_id)
    tables = _load_tables(directory, found.blob.fields)
    indexed = index_tables(tables)
    skip = {path_id for path_id, _count in found.candidates}
    skip.add(found.path_id)
    objects = collect_objects(bundle, skip)
    matches = _flatten_matches(indexed)
    report = {
        "build_id": identity.build_id,
        "unity_version": identity.unity_version,
        "database": {
            "assets_file": assets_file,
            "path_id": found.path_id,
            "candidates": [
                {"path_id": path_id, "units": count} for path_id, count in found.candidates
            ],
        },
        "tables": indexed,
        "table_matches": matches,
        "objects": objects,
    }
    path = cfg.cache_dir / "survey" / identity.build_id / "report.json"
    write_json(path, report)
    _print_report(report, path)
    return path


def collect_objects(bundle: Path, skip_path_ids: set[int]) -> list[dict]:
    """Parse MonoBehaviour and TextAsset objects in every assets file."""
    index = read_index(bundle)
    found: list[dict] = []

    def on_file(name: str, data: bytes) -> bool:
        try:
            env = load_bytes(data)
        except PipelineError:
            raise
        except Exception as exc:
            print(f"  {name}: {exc}", flush=True)
            return False
        try:
            for obj in env.objects:
                if obj.path_id in skip_path_ids:
                    continue
                type_name = obj.type.name
                if type_name not in ("MonoBehaviour", "TextAsset"):
                    continue
                try:
                    entry = _catalog_unity_object(obj, type_name)
                except Exception as exc:
                    print(f"  skip {name} path_id={obj.path_id}: {exc}", flush=True)
                    continue
                if entry is None:
                    continue
                found.append(
                    {
                        "assets_file": name,
                        "path_id": obj.path_id,
                        "type": type_name,
                        **entry,
                    }
                )
        finally:
            del env
            gc.collect()
        return False

    scan_assets(index, on_file)
    found.sort(key=lambda item: (item["assets_file"], item["path_id"]))
    return found


def _catalog_unity_object(obj, type_name: str) -> dict | None:
    raw = obj.get_raw_data()
    has_tree = bool(getattr(obj, "serialized_type", None) and obj.serialized_type.nodes)
    tree = _maybe_tree(obj, raw, has_tree)
    if type_name == "TextAsset":
        return catalog_text_asset(
            raw,
            typetree=tree,
            byte_size=obj.byte_size,
            typetree_present=has_tree,
        )
    return catalog_monobehaviour(
        raw,
        typetree=tree,
        byte_size=obj.byte_size,
        typetree_present=has_tree,
    )


def _maybe_tree(obj, raw: bytes, has_tree: bool) -> dict | None:
    if not has_tree:
        return None
    if obj.byte_size > _SMALL_OBJECT and not _raw_may_match(raw):
        return None
    try:
        tree = obj.read_typetree(check_read=False)
    except Exception:
        return None
    if isinstance(tree, dict):
        return tree
    return None


def _raw_may_match(raw: bytes) -> bool:
    folded = raw.lower()
    needles = [word.encode("ascii") for word in _WORDS]
    needles.extend((b"lineofsight", b"buff", b"fow", b"fowl"))
    return any(needle in folded for needle in needles)


def _load_tables(directory: Path, fields: dict[str, str]) -> dict:
    paths = [directory / f"{field}.json" for field in FIELD_ORDER]
    if all(path.is_file() for path in paths):
        print(f"reading tables from {directory}", flush=True)
        return {field: load_table(directory, field) for field in FIELD_ORDER}
    print("decrypting the 24 tables in memory", flush=True)
    tables = {}
    for field in FIELD_ORDER:
        try:
            tables[field] = json.loads(aes_decrypt(fields[field]))
        except Exception as exc:
            raise PipelineError(f"{field} did not decrypt to JSON: {exc}") from exc
    return tables


def _index_table(field: str, value) -> dict:
    if isinstance(value, list):
        rows = [row for row in value if isinstance(row, dict)]
        row_count = len(value)
    elif isinstance(value, dict):
        rows = [value]
        row_count = 1
    else:
        rows = []
        row_count = 0
    keys: set[str] = set()
    for row in rows:
        keys.update(str(key) for key in row)
    ordered = sorted(keys, key=str.lower)
    matches = [_summarize_column(rows, key) for key in ordered if interesting(key)]
    return {
        "field": field,
        "file": FIELD_TO_FILE.get(field, field),
        "rows": row_count,
        "keys": ordered,
        "matches": matches,
    }


def _summarize_column(rows: list[dict], key: str) -> dict:
    values = []
    examples = []
    for row in rows:
        if key not in row:
            continue
        value = row[key]
        values.append(value)
        if len(examples) < _MAX_EXAMPLES:
            example = {"value": _brief(value)}
            if "Id" in row:
                example = {"id": row["Id"], "value": _brief(value)}
            examples.append(example)
    summary: dict = {"key": key, "examples": examples}
    if not values or any(not _primitive(value) for value in values):
        summary["distinct_count"] = len(values)
        return summary
    distinct: list = []
    seen: set[str] = set()
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        distinct.append(value)
    summary["distinct_count"] = len(distinct)
    numbers = [value for value in values if _number(value)]
    if len(numbers) == len(values):
        summary["min"] = min(numbers)
        summary["max"] = max(numbers)
    short = all(not isinstance(value, str) or len(value) <= 80 for value in distinct)
    if len(distinct) <= _MAX_DISTINCT and short:
        summary["distinct"] = distinct
    return summary


def _flatten_matches(indexed: list[dict]) -> list[dict]:
    flat = []
    for table in indexed:
        for match in table["matches"]:
            flat.append({"field": table["field"], "file": table["file"], **match})
    return flat


def _assemble(
    *,
    name: str | None,
    script: tuple[int, int] | None,
    strings: list[str],
    byte_size: int,
    typetree: dict | None,
    typetree_present: bool,
) -> dict | None:
    if typetree is not None:
        tree_name = typetree.get("m_Name")
        if name is None and isinstance(tree_name, str):
            name = tree_name
    if name == OBJECT_NAME:
        return None

    aes: list[dict] = []
    plain: list[str] = []
    docs: list = []
    seen: set[str] = set()
    for text in strings:
        if text == name or text in seen:
            continue
        seen.add(text)
        _consider_text(text, aes, plain, docs)

    matches = _field_matches(typetree) if typetree is not None else []
    name_hit = bool(name) and interesting(name)
    docs_hit = any(_json_interesting(doc) for doc in docs)
    if not (name_hit or aes or plain or docs_hit or matches):
        return None

    file_id = script[0] if script is not None else None
    path_id = script[1] if script is not None else None
    entry: dict = {
        "m_name": name,
        "script_file_id": file_id,
        "script_path_id": path_id,
        "byte_size": byte_size,
        "typetree": typetree_present,
    }
    if aes:
        entry["aes"] = aes
    if plain:
        entry["plaintext"] = plain[:_MAX_PLAINTEXT]
    if matches:
        entry["field_matches"] = matches
    _store_docs(entry, docs)
    if typetree is not None and byte_size <= _SMALL_OBJECT:
        safe = _json_safe(typetree)
        encoded = json.dumps(safe, ensure_ascii=False)
        if len(encoded) <= _SMALL_JSON:
            entry["fields"] = safe
    if not _has_payload(entry):
        entry["numeric_fields"] = "not in the blob"
    return entry


def _consider_text(text: str, aes: list[dict], plain: list[str], docs: list) -> None:
    stripped = text.strip()
    if has_marker(stripped):
        aes.append(_decrypt_blob(stripped))
        return
    parsed = _maybe_json(stripped)
    if parsed is not None:
        _collect_aes(parsed, aes)
        docs.append(parsed)
        return
    if interesting(text) and len(plain) < _MAX_PLAINTEXT:
        plain.append(text[:200])


def _decrypt_blob(wire: str) -> dict:
    try:
        plaintext = aes_decrypt(wire)
    except Exception as exc:
        return {"error": str(exc)}
    try:
        parsed = json.loads(plaintext)
    except json.JSONDecodeError:
        preview = plaintext.decode("utf-8", errors="replace")[:200]
        return {"error": "not json", "bytes": len(plaintext), "text": preview}
    item: dict = {"keys": _json_keys(parsed)}
    if isinstance(parsed, list):
        item["rows"] = len(parsed)
    encoded = json.dumps(parsed, ensure_ascii=False)
    if len(encoded) <= _SMALL_JSON:
        item["json"] = parsed
    return item


def _collect_aes(value, aes: list[dict]) -> None:
    if isinstance(value, str) and has_marker(value.strip()):
        aes.append(_decrypt_blob(value.strip()))
    elif isinstance(value, dict):
        for item in value.values():
            _collect_aes(item, aes)
    elif isinstance(value, list):
        for item in value:
            _collect_aes(item, aes)


def _maybe_json(text: str):
    if not text or text[0] not in "[{":
        return None
    if len(text) > _MAX_STRING:
        return {"omitted": True, "bytes": len(text)}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _store_docs(entry: dict, docs: list) -> None:
    if not docs:
        return
    stored = []
    for doc in docs:
        if isinstance(doc, dict) and doc.get("omitted"):
            stored.append(doc)
            continue
        encoded = json.dumps(doc, ensure_ascii=False)
        if len(encoded) <= _SMALL_JSON:
            stored.append(doc)
        elif isinstance(doc, (dict, list)):
            stored.append({"keys": _json_keys(doc), "rows": len(doc) if isinstance(doc, list) else 1})
    if not stored:
        return
    entry["json"] = stored[0] if len(stored) == 1 else stored


def _json_keys(value) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value]
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            if isinstance(item, dict):
                keys.update(str(key) for key in item)
        return sorted(keys)
    return []


def _json_interesting(value) -> bool:
    if isinstance(value, dict):
        if value.get("omitted"):
            return False
        return any(interesting(str(key)) or _json_interesting(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_json_interesting(item) for item in value[:50])
    if isinstance(value, str):
        return len(value) <= 200 and interesting(value)
    return False


def _field_matches(tree: dict) -> list[dict]:
    matches: list[dict] = []

    def walk(node, path: str, depth: int) -> None:
        if depth > 8 or len(matches) >= 100:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                child = f"{path}.{key}" if path else str(key)
                if interesting(str(key)):
                    matches.append({"path": child, "value": _brief(value)})
                walk(value, child, depth + 1)
        elif isinstance(node, list):
            for index, value in enumerate(node[:32]):
                walk(value, f"{path}[{index}]", depth + 1)

    walk(tree, "", 0)
    return matches


def _has_payload(entry: dict) -> bool:
    if entry.get("aes") or entry.get("json") is not None or entry.get("fields") is not None:
        return True
    for match in entry.get("field_matches") or []:
        if _number(match.get("value")):
            return True
    return False


def _text_asset_name(raw: bytes) -> str | None:
    try:
        name, _start, _end = _read_string(raw, 0)
    except (ValueError, UnicodeDecodeError):
        return None
    if len(name) > 200 or name[:1] in "[{":
        return None
    return name


def _parse_header(raw: bytes) -> tuple[str, tuple[int, int]] | None:
    try:
        _game_object, offset = _read_pptr(raw, 0)
        _enabled, offset = _read_int(raw, offset)
        script, offset = _read_pptr(raw, offset)
        name, _start, _end = _read_string(raw, offset)
    except (ValueError, UnicodeDecodeError):
        return None
    return name, script


def _iter_unity_strings(raw: bytes) -> list[str]:
    found: list[str] = []
    offset = 0
    size = len(raw)
    occupied = 0
    while offset + 4 <= size:
        if offset < occupied:
            offset = (occupied + 3) & ~3
            continue
        parsed = _try_string(raw, offset)
        if parsed is None:
            offset += 4
            continue
        text, end = parsed
        found.append(text)
        occupied = end
        offset = end
    return found


def _try_string(raw: bytes, offset: int) -> tuple[str, int] | None:
    try:
        text, _start, end = _read_string(raw, offset)
    except (ValueError, UnicodeDecodeError):
        return None
    if not text or len(text) > _MAX_STRING:
        return None
    if any(ord(ch) < 32 and ch not in "\t\n\r" for ch in text):
        return None
    return text, end


def _read_pptr(raw: bytes, offset: int) -> tuple[tuple[int, int], int]:
    if offset + 12 > len(raw):
        raise ValueError("truncated PPtr")
    file_id = struct.unpack_from("<I", raw, offset)[0]
    path_id = struct.unpack_from("<q", raw, offset + 4)[0]
    return (file_id, path_id), offset + 12


def _read_int(raw: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(raw):
        raise ValueError("truncated int")
    return struct.unpack_from("<i", raw, offset)[0], offset + 4


def _read_string(raw: bytes, offset: int) -> tuple[str, int, int]:
    if offset + 4 > len(raw):
        raise ValueError("truncated string length")
    length = struct.unpack_from("<i", raw, offset)[0]
    if length < 0 or length > _MAX_STRING or offset + 4 + length > len(raw):
        raise ValueError("bad string length")
    blob = raw[offset + 4 : offset + 4 + length]
    if length > 256 and not _mostly_text(blob):
        raise ValueError("not text")
    text = blob.decode("utf-8")
    end = (offset + 4 + length + 3) & ~3
    if end > len(raw):
        raise ValueError("truncated string padding")
    return text, offset, end


def _mostly_text(blob: bytes) -> bool:
    sample = blob[:64]
    return all(byte in (9, 10, 13) or byte >= 32 for byte in sample)


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for part in re.findall(r"[A-Za-z0-9]+", text):
        pieces = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", part)
        tokens.extend(piece.lower() for piece in (pieces or [part]))
    return tokens


def _primitive(value) -> bool:
    return value is None or isinstance(value, (str, bool, int, float))


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _brief(value):
    if isinstance(value, str):
        return value[:120]
    if _primitive(value):
        if isinstance(value, float) and value != value:
            return None
        return value
    if isinstance(value, list):
        return {"type": "list", "length": len(value)}
    if isinstance(value, dict):
        return {"type": "object", "keys": [str(key) for key in list(value)[:20]]}
    if isinstance(value, (bytes, bytearray)):
        return f"<{len(value)} bytes>"
    return str(value)


def _json_safe(value, depth: int = 0):
    if depth > 12:
        return "<nested>"
    if isinstance(value, str):
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return f"<{len(value)} bytes>"
    if isinstance(value, dict):
        return {str(key): _json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, depth + 1) for item in value]
    return str(value)


def _print_report(report: dict, path: Path) -> None:
    print(f"build {report['build_id']}", flush=True)
    matches = report["table_matches"]
    print(f"table matches: {len(matches)}", flush=True)
    for match in matches:
        print(f"  {match['field']}.{match['key']} {_match_brief(match)}", flush=True)
    objects = report["objects"]
    valued = [obj for obj in objects if _worth_opening(obj)]
    bare = [obj for obj in objects if not _worth_opening(obj)]
    print(f"other objects: {len(valued)}", flush=True)
    for obj in valued:
        print(
            f"  {obj['type']} {obj['m_name']!r} file={obj['assets_file']} "
            f"path_id={obj['path_id']} {_object_brief(obj)}",
            flush=True,
        )
    print(f"names without numbers: {len(bare)}", flush=True)
    for obj in bare:
        print(
            f"  {obj['type']} {obj['m_name']!r} file={obj['assets_file']} "
            f"path_id={obj['path_id']} script={obj['script_path_id']}",
            flush=True,
        )
    print(f"wrote {path}", flush=True)


def _worth_opening(obj: dict) -> bool:
    if obj.get("aes") or obj.get("json") is not None or obj.get("fields") is not None:
        return True
    return any(_number(match.get("value")) for match in obj.get("field_matches") or [])


def _match_brief(match: dict) -> str:
    if "distinct" in match:
        rendered = json.dumps(match["distinct"], ensure_ascii=False)
        return f"distinct={rendered}"
    bits = []
    if "min" in match:
        bits.append(f"min={match['min']}")
        bits.append(f"max={match['max']}")
    if "distinct_count" in match:
        bits.append(f"distinct={match['distinct_count']}")
    examples = match.get("examples") or []
    if examples:
        bits.append("examples=" + json.dumps(examples[:3], ensure_ascii=False))
    return " ".join(bits)


def _object_brief(obj: dict) -> str:
    parts = []
    keys: list[str] = []
    for item in obj.get("aes") or []:
        keys.extend(item.get("keys") or [])
    if keys:
        parts.append("aes=" + ",".join(keys[:12]))
    elif obj.get("aes"):
        parts.append("aes")
    if obj.get("json") is not None:
        parts.append("json")
    if obj.get("fields") is not None:
        parts.append("fields")
    matches = obj.get("field_matches") or []
    if matches:
        parts.append("fields=" + ",".join(item["path"] for item in matches[:8]))
    return " ".join(parts)
