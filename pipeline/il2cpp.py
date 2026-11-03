"""Read BuildingsConfig, FowOfWarConfig, Buff Config, and FOWToolConfig.

Il2CppDumper restores field names. The asset blobs have no typetree, so the
values are walked from those fields. A walk that does not consume the object
does not invent numbers.
"""

from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
from pathlib import Path

from pipeline.bundle import identify_bundle
from pipeline.bundle_stream import extract_file, load_bytes, read_index
from pipeline.config import Config, require_bundle
from pipeline.errors import PipelineError
from pipeline.snapshot import write_json

METADATA_MAGIC = 0xFAB11BAF
_ASSETS = "globalgamemanagers.assets"
_SMALL_OBJECT = 4096
_RELATED_LIMIT = 200

# Asset m_Name values, and the class name used in dump.cs when it differs.
ASSET_CLASSES = {
    "BuildingsConfig": "BuildingsConfig",
    "FowOfWarConfig": "FogOfWarConfig",
    "Buff Config": "BuffConfig",
    "FOWToolConfig": "FOWToolConfig",
}
CLASS_NAMES = frozenset(ASSET_CLASSES.values())
_CLASS_ORDER = ("BuildingsConfig", "FogOfWarConfig", "BuffConfig", "FOWToolConfig")
_METHOD_WORDS = ("stealth", "cover", "forest", "suppress", "building", "fow")

_CLASS_LINE = re.compile(
    r"^(?:public |internal |private |protected |protected internal )?"
    r"(?:(?:static|abstract|sealed|unsafe)\s+)*"
    r"(?P<kind>class|struct|enum)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_.]*)"
    r"(?:<(?P<own_generic>[^>]+)>)?"
    r"(?:\s*:\s*(?P<base>[A-Za-z_][A-Za-z0-9_.]*)(?:<(?P<base_generic>[^>]+)>)?(?:\s*,.*)?)?"
    r"(?:\s*//\s*TypeDefIndex:\s*\d+)?"
    r"\s*\{?\s*$"
)
_FIELD_BODY = re.compile(
    r"(?P<type>.+?)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*=\s*.*)?;\s*(?://\s*(?P<offset>0x[0-9A-Fa-f]+))?\s*$"
)
_MODIFIERS = (
    "protected internal ",
    "public ",
    "private ",
    "protected ",
    "internal ",
    "static ",
    "const ",
    "readonly ",
    "new ",
    "volatile ",
)
_PPTR_BASES = frozenset(
    {
        "Object",
        "GameObject",
        "Component",
        "Behaviour",
        "MonoBehaviour",
        "ScriptableObject",
    }
)
# Sirenix.Serialization.DataFormat is a 4-byte enum. A protobuf enum earlier
# in dump.cs uses the same short name, so this field is not looked up there.
_SIRENIX_INT_ENUMS = frozenset({"DataFormat"})
_ODIN_NAMES = ("ShowWeaponRangesByRelation", "LowHighAltRangeWeapons")
_ODIN_BASE = "SerializedScriptableObject"
_STRUCTS = {
    "Vector2": ("float", "float"),
    "Vector3": ("float", "float", "float"),
    "Vector4": ("float", "float", "float", "float"),
    "Quaternion": ("float", "float", "float", "float"),
    "Color": ("float", "float", "float", "float"),
    "Rect": ("float", "float", "float", "float"),
}
_PRIMITIVE = {
    "bool": "bool",
    "Boolean": "bool",
    "float": "float",
    "Single": "float",
    "int": "int",
    "Int32": "int",
    "string": "string",
    "String": "string",
    "byte": "byte",
    "Byte": "byte",
    "sbyte": "byte",
    "SByte": "byte",
    "short": "short",
    "Int16": "short",
    "ushort": "short",
    "UInt16": "short",
}


def assembly_path(cfg: Config) -> Path:
    """GameAssembly.dll sits next to BrokenArrow.exe, in game_root."""
    return cfg.game_root / "GameAssembly.dll"


def metadata_path(cfg: Config) -> Path:
    return cfg.game_root / "BrokenArrow_Data" / "il2cpp_data" / "Metadata" / "global-metadata.dat"


def read_metadata_version(path: Path) -> int:
    """Return the metadata version. The file must start with the IL2CPP magic."""
    try:
        header = path.read_bytes()[:8]
    except OSError as exc:
        raise PipelineError(f"cannot read {path}: {exc}") from exc
    if len(header) < 8:
        raise PipelineError(f"{path} is too small to be global-metadata")
    magic, version = struct.unpack("<II", header)
    if magic != METADATA_MAGIC:
        raise PipelineError(f"{path} is not global-metadata (magic {magic:#x})")
    return version


def extract_classes(text: str) -> dict:
    """Cut the cover classes and matching method signatures out of dump.cs text."""
    return extract_class_lines(text.splitlines())


def extract_class_lines(lines) -> dict:
    """Stream dump.cs. Cover classes keep fields and matching methods.

    Other classes are kept only as type layouts so a serialized dictionary,
    struct, or enum can be walked. A walk still has to end on the last byte.
    """
    enums: dict[str, str] = {}
    types: dict[str, dict] = {}
    classes: dict[str, dict] = {}
    related: list[dict] = []
    omitted = 0
    depth = 0
    current_name: str | None = None
    current: dict | None = None
    current_enum: str | None = None
    attributes: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if depth == 0:
            if line.strip() == "{":
                depth = 1
                continue
            match = _CLASS_LINE.match(line)
            if match is not None:
                name = match.group("name").split(".")[-1]
                current_name = name
                current_enum = None
                attributes = []
                if match.group("kind") == "enum":
                    enums.setdefault(name, "int")
                    current_enum = name
                    current = None
                else:
                    base = match.group("base")
                    record = types.get(name)
                    if record is None:
                        record = {
                            "name": name,
                            "base": base.split(".")[-1] if base else None,
                            "own_generic": _split_generic(match.group("own_generic")),
                            "base_args": _split_generic(match.group("base_generic")),
                            "fields": [],
                            "methods": [],
                        }
                        types[name] = record
                    current = record
                    if name in CLASS_NAMES:
                        classes[name] = record
                if "{" in line:
                    depth = 1
            continue

        stripped = line.strip()
        if stripped.startswith("[") and depth == 1:
            attributes.append(stripped)
        elif line.startswith("\t") and not line.startswith("\t//") and depth == 1:
            field = _parse_field(line)
            if field is not None and "(" not in line:
                field["serialized"] = _marked_serialized(field, attributes)
                attributes = []
                if current_enum is not None and field["name"] == "value__":
                    enums[current_enum] = _PRIMITIVE.get(field["type"].split(".")[-1], "int")
                elif current is not None:
                    current["fields"].append(field)
            else:
                signature = _parse_method(line)
                if signature is not None and current_name is not None:
                    attributes = []
                    method_name = _method_name(signature)
                    if _method_interesting(method_name):
                        if current is not None and current_name in CLASS_NAMES:
                            current["methods"].append(signature)
                        elif len(related) < _RELATED_LIMIT:
                            related.append({"class": current_name, "signature": signature})
                        else:
                            omitted += 1

        depth += line.count("{") - line.count("}")
        if depth <= 0:
            depth = 0
            current_name = None
            current = None
            current_enum = None
            attributes = []

    ordered = [classes[name] for name in _CLASS_ORDER if name in classes]
    return {
        "enums": enums,
        "types": types,
        "classes": ordered,
        "related_methods": related,
        "related_methods_omitted": omitted,
    }


def decode_fields(
    raw: bytes,
    fields: list[dict],
    enums: set[str] | dict[str, str] | None = None,
    types: dict | None = None,
    base: str | None = None,
) -> dict | None:
    """Walk serialized fields after m_Name. Return None unless the walk ends on the last byte."""
    enum_map = _enum_map(enums)
    type_map = types or {}
    fields = _with_odin_prefix(fields, base, type_map)
    successes: list[dict] = []
    for public_only in (False, True):
        for hashset_as_list in (False, True):
            chosen = [field for field in fields if _is_serialized(field, public_only)]
            try:
                values, offset = _walk(raw, chosen, enum_map, type_map, hashset_as_list)
            except (ValueError, struct.error, KeyError, RecursionError):
                continue
            if offset == len(raw):
                successes.append(_note_odin_collections(values))
    unique = []
    for values in successes:
        if values not in unique:
            unique.append(values)
    if len(unique) == 1:
        return unique[0]
    return None


def write_il2cpp(cfg: Config) -> Path:
    """Dump GameAssembly and write cache/il2cpp/<build-id>/configs.json."""
    bundle = require_bundle(cfg)
    binary = assembly_path(cfg)
    metadata = metadata_path(cfg)
    if not binary.is_file():
        raise PipelineError(
            f"missing {binary}. GameAssembly.dll belongs in game_root, next to BrokenArrow.exe."
        )
    if not metadata.is_file():
        raise PipelineError(f"missing {metadata}")
    version = read_metadata_version(metadata)
    identity = identify_bundle(bundle, cfg.cache_dir)
    directory = cfg.cache_dir / "il2cpp" / identity.build_id
    directory.mkdir(parents=True, exist_ok=True)
    dump_path = directory / "dump.cs"
    if dump_path.is_file() and dump_path.stat().st_size > 0:
        print(f"dump {identity.build_id} already exists", flush=True)
    else:
        exe = ensure_dumper(cfg.repo_root, cfg.cache_dir)
        _run_dumper(exe, binary, metadata, directory)
        if not dump_path.is_file() or dump_path.stat().st_size == 0:
            raise PipelineError(f"Il2CppDumper did not write {dump_path}")
    print(f"metadata version {version}", flush=True)
    print(f"reading {dump_path}", flush=True)
    with dump_path.open(encoding="utf-8", errors="replace") as handle:
        extracted = extract_class_lines(handle)
    objects = _read_config_objects(bundle)
    report = _build_report(identity.build_id, version, extracted, objects)
    path = directory / "configs.json"
    write_json(path, report)
    _print_report(report, path)
    return path


def ensure_dumper(repo: Path, cache_dir: Path) -> Path:
    """Build the vendored v39 dumper into cache and disable its exit prompt there."""
    destination = cache_dir / "tools" / "Il2CppDumper"
    exe = destination / "Il2CppDumper.exe"
    project = repo / "thirdparty-tools" / "Il2CppDumper-master" / "Il2CppDumper" / "Il2CppDumper.csproj"
    if not exe.is_file():
        if not project.is_file():
            raise PipelineError(f"missing {project}")
        destination.mkdir(parents=True, exist_ok=True)
        print(f"building {project.name}", flush=True)
        completed = subprocess.run(
            ["dotnet", "build", str(project), "-c", "Release", "-f", "net8.0", "-o", str(destination)],
            check=False,
            text=True,
            capture_output=True,
        )
        for name in ("bin", "obj"):
            folder = project.parent / name
            if folder.is_dir():
                shutil.rmtree(folder)
        if completed.returncode != 0 or not exe.is_file():
            detail = (completed.stdout + completed.stderr)[-2000:]
            raise PipelineError(f"Il2CppDumper build failed.\n{detail}")
    _disable_prompt(destination / "config.json")
    return exe


def _disable_prompt(path: Path) -> None:
    if not path.is_file():
        raise PipelineError(f"missing {path}")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if loaded.get("RequireAnyKey") is False:
        return
    loaded["RequireAnyKey"] = False
    path.write_text(json.dumps(loaded, indent=2) + "\n", encoding="utf-8")


def _run_dumper(exe: Path, binary: Path, metadata: Path, directory: Path) -> None:
    print(f"dumping {binary.name} into {directory}", flush=True)
    process = subprocess.Popen(
        [str(exe), str(binary), str(metadata), str(directory)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    captured: list[str] = []
    for line in process.stdout:
        print(line, end="", flush=True)
        captured.append(line)
    code = process.wait()
    text = "".join(captured)
    if code != 0 or "ERROR:" in text or "NotSupportedException" in text:
        tail = text[-2000:]
        raise PipelineError(f"Il2CppDumper failed (exit {code}).\n{tail}")


def _read_config_objects(bundle: Path) -> list[dict]:
    index = read_index(bundle)
    print(f"extracting {_ASSETS}", flush=True)
    data = extract_file(index, _ASSETS)
    env = load_bytes(data)
    found: list[dict] = []
    try:
        for obj in env.objects:
            if obj.type.name != "MonoBehaviour" or obj.byte_size > _SMALL_OBJECT:
                continue
            raw = obj.get_raw_data()
            header = _parse_header(raw)
            if header is None or header[0] not in ASSET_CLASSES:
                continue
            found.append(
                {
                    "m_name": header[0],
                    "class_name": ASSET_CLASSES[header[0]],
                    "path_id": obj.path_id,
                    "script_path_id": header[1][1],
                    "byte_size": len(raw),
                    "raw": raw,
                }
            )
    finally:
        del env
    found.sort(key=lambda item: (item["class_name"], item["path_id"]))
    return found


def _build_report(build_id: str, version: int, extracted: dict, objects: list[dict]) -> dict:
    by_class = {item["name"]: item for item in extracted["classes"]}
    enums = set(extracted["enums"])
    grouped: dict[str, list[dict]] = {}
    for obj in objects:
        grouped.setdefault(obj["class_name"], []).append(obj)
    decoded_objects = []
    for class_name, group in grouped.items():
        class_info = by_class.get(class_name)
        fields = class_info["fields"] if class_info else []
        first = group[0]["raw"]
        for obj in group:
            values = (
                decode_fields(
                    obj["raw"],
                    fields,
                    extracted["enums"],
                    extracted.get("types"),
                    base=class_info.get("base") if class_info else None,
                )
                if fields
                else None
            )
            entry = {
                "m_name": obj["m_name"],
                "class": class_name,
                "path_id": obj["path_id"],
                "script_path_id": obj["script_path_id"],
                "byte_size": obj["byte_size"],
                "decoded": values is not None,
                "values": values,
                "same_bytes_as": None,
            }
            if obj is not group[0]:
                entry["same_bytes_as"] = group[0]["path_id"] if obj["raw"] == first else None
            decoded_objects.append(entry)
    return {
        "build_id": build_id,
        "metadata_version": version,
        "classes": extracted["classes"],
        "related_methods": extracted["related_methods"],
        "related_methods_omitted": extracted["related_methods_omitted"],
        "objects": decoded_objects,
    }


def _print_report(report: dict, path: Path) -> None:
    print(f"build {report['build_id']} metadata {report['metadata_version']}", flush=True)
    for obj in report["objects"]:
        same = ""
        if obj["same_bytes_as"] is not None:
            same = f" same_bytes_as={obj['same_bytes_as']}"
        elif obj["same_bytes_as"] is None and any(
            other["m_name"] == obj["m_name"] and other["path_id"] != obj["path_id"] for other in report["objects"]
        ):
            pass
        print(
            f"{obj['m_name']} path_id={obj['path_id']} bytes={obj['byte_size']} "
            f"decoded={obj['decoded']}{same}",
            flush=True,
        )
        if obj["values"]:
            for name, value in obj["values"].items():
                print(f"  {name} = {json.dumps(value, ensure_ascii=False)}", flush=True)
        else:
            class_info = next((item for item in report["classes"] if item["name"] == obj["class"]), None)
            for field in (class_info or {}).get("fields", []):
                print(f"  {field['type']} {field['name']}", flush=True)
    print(f"wrote {path}", flush=True)


def _parse_field(line: str) -> dict | None:
    rest = line[1:] if line.startswith("\t") else line
    if "(" in rest:
        return None
    modifiers: list[str] = []
    while True:
        for word in _MODIFIERS:
            if rest.startswith(word):
                modifiers.append(word.strip())
                rest = rest[len(word) :]
                break
        else:
            break
    match = _FIELD_BODY.match(rest)
    if match is None:
        return None
    return {
        "access": next((item for item in modifiers if item in {"public", "private", "protected", "internal", "protected internal"}), ""),
        "static": "static" in modifiers,
        "const": "const" in modifiers,
        "type": match.group("type").strip(),
        "name": match.group("name"),
        "offset": match.group("offset"),
    }


def _parse_method(line: str) -> str | None:
    stripped = line.strip()
    if "(" not in stripped or stripped.startswith("//") or stripped.startswith("["):
        return None
    if stripped.endswith(" { }"):
        return stripped[: -len(" { }")]
    if stripped.endswith(";"):
        return stripped
    return None


def _method_name(signature: str) -> str:
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", signature)
    return match.group(1) if match else ""


def _method_interesting(name: str) -> bool:
    folded = name.lower()
    return any(word in folded for word in _METHOD_WORDS)


def _is_serialized(field: dict, public_only: bool) -> bool:
    if field.get("static") or field.get("const"):
        return False
    marked = field.get("serialized")
    if marked is False:
        return False
    access = field.get("access") or ""
    if marked is None and access not in {"public", ""}:
        return False
    if marked is True and access not in {"public", ""} and public_only:
        return False
    if public_only and access not in {"public", ""}:
        return False
    return True


def _with_odin_prefix(fields: list[dict], base: str | None, types: dict) -> list[dict]:
    """SerializedScriptableObject stores Odin data before the class fields."""
    if not _inherits_odin(base, types):
        return fields
    prefix = {
        "access": "private",
        "static": False,
        "const": False,
        "serialized": True,
        "type": "SerializationData",
        "name": "serializationData",
    }
    return [prefix, *fields]


def _inherits_odin(base: str | None, types: dict) -> bool:
    seen: set[str] = set()
    current = base
    while current and current not in seen:
        if current == _ODIN_BASE:
            return True
        seen.add(current)
        info = types.get(current)
        current = info.get("base") if info else None
    return False


def _odin_collection(type_name: str) -> bool:
    simple = type_name.split(".")[-1]
    return (simple.startswith("HashSet<") and simple.endswith(">")) or (
        simple.startswith("Dictionary<") and simple.endswith(">")
    )


def _note_odin_collections(values: dict) -> dict:
    """Name the two collections inside the Odin payload. Do not parse Binary."""
    data = values.get("serializationData")
    if not isinstance(data, dict):
        return values
    fmt = data.get("SerializedFormat")
    nodes = data.get("SerializationNodes") if isinstance(data.get("SerializationNodes"), list) else []
    payload = _payload_bytes(data.get("SerializedBytes"))
    noted = dict(values)
    for name in _ODIN_NAMES:
        if name not in noted:
            continue
        if fmt == 2:
            matched = [node for node in nodes if isinstance(node, dict) and node.get("Name") == name]
            noted[name] = {"undecoded": True, "nodes": matched}
        elif fmt == 0:
            noted[name] = {"undecoded": True, "in_payload": name.encode("utf-8") in payload}
    return noted


def _payload_bytes(value) -> bytes:
    if isinstance(value, list) and all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        return bytes(item & 0xFF for item in value)
    return b""


def _walk(raw: bytes, fields: list[dict], enums: dict[str, str], types: dict, hashset_as_list: bool) -> tuple[dict, int]:
    header = _parse_header(raw)
    if header is None:
        raise ValueError("header")
    offset = header[2]
    values, offset = _read_fields(raw, offset, fields, enums, types, hashset_as_list, {})
    return values, offset


def _read_fields(raw, offset, fields, enums, types, hashset_as_list, generic: dict):
    values: dict = {}
    for field in fields:
        type_name = _substitute(field["type"], generic)
        if _odin_collection(type_name):
            values[field["name"]] = {"undecoded": True}
            continue
        value, offset = _read_type(raw, offset, type_name, enums, types, hashset_as_list)
        values[field["name"]] = value
    return values, offset


def _read_type(raw, offset, type_name, enums, types, hashset_as_list):
    type_name = type_name.strip()
    offset = _align(offset)
    list_item = _list_element(type_name)
    if list_item is not None:
        return _read_array(raw, offset, list_item, enums, types, hashset_as_list)
    if type_name.startswith("HashSet<") and type_name.endswith(">"):
        if not hashset_as_list:
            raise ValueError(type_name)
        return _read_array(raw, offset, type_name[len("HashSet<") : -1], enums, types, hashset_as_list)
    simple = type_name.split(".")[-1]
    if simple in _SIRENIX_INT_ENUMS:
        return _read_value(raw, offset, "int")
    if simple in _STRUCTS:
        values = []
        for kind in _STRUCTS[simple]:
            value, offset = _read_value(raw, _align(offset), kind)
            values.append(value)
        return values, offset
    primitive = _PRIMITIVE.get(simple)
    if primitive is not None:
        return _read_value(raw, offset, primitive)
    if simple in enums or type_name in enums:
        kind = enums.get(simple) or enums.get(type_name) or "int"
        return _read_value(raw, offset, kind)
    if _is_pptr(simple, types):
        pointer, offset = _read_pptr(raw, offset)
        return {"file_id": pointer[0], "path_id": pointer[1]}, offset
    info = types.get(simple)
    if info is None:
        raise ValueError(type_name)
    return _read_inline(raw, offset, info, enums, types, hashset_as_list)


def _read_inline(raw, offset, info, enums, types, hashset_as_list):
    fields, generic = _expanded_fields(info, types, set())
    return _read_fields(raw, offset, fields, enums, types, hashset_as_list, generic)


def _expanded_fields(info: dict, types: dict, seen: set[str]) -> tuple[list[dict], dict]:
    name = info["name"]
    if name in seen:
        return [], {}
    seen.add(name)
    generic = {}
    inherited: list[dict] = []
    base_name = info.get("base")
    if base_name and base_name in types and base_name not in _PPTR_BASES and base_name not in {"Dictionary", "List", "HashSet", "ValueType"}:
        base = types[base_name]
        generic = dict(zip(base.get("own_generic") or [], info.get("base_args") or []))
        inherited, _base_generic = _expanded_fields(base, types, seen)
        inherited = [_with_type(_substitute(field["type"], generic), field) for field in inherited]
    own = [field for field in info.get("fields", []) if _is_serialized(field, public_only=False)]
    return inherited + own, generic


def _with_type(type_name: str, field: dict) -> dict:
    copied = dict(field)
    copied["type"] = type_name
    return copied


def _read_array(raw, offset, element, enums, types, hashset_as_list):
    offset = _align(offset)
    if offset + 4 > len(raw):
        raise ValueError("array")
    count = struct.unpack_from("<i", raw, offset)[0]
    offset += 4
    if count < 0 or count > 100000:
        raise ValueError("array length")
    primitive = _packed_primitive(element, enums)
    if primitive in {"byte", "bool"}:
        if offset + count > len(raw):
            raise ValueError("array")
        blob = raw[offset : offset + count]
        offset = _align(offset + count)
        if primitive == "bool":
            return [bool(item) for item in blob], offset
        return list(blob), offset
    values = []
    for _index in range(count):
        value, offset = _read_type(raw, offset, element, enums, types, hashset_as_list)
        values.append(value)
    return values, offset


def _is_pptr(name: str, types: dict) -> bool:
    if name in _PPTR_BASES or name in {"GameObject", "Texture2D", "Sprite", "Material", "AudioClip", "Transform"}:
        return True
    seen: set[str] = set()
    current = name
    while current and current not in seen:
        seen.add(current)
        if current in _PPTR_BASES:
            return True
        info = types.get(current)
        if info is None:
            return False
        current = info.get("base")
    return False


def _list_element(type_name: str) -> str | None:
    if type_name.endswith("[]"):
        return type_name[:-2]
    if type_name.startswith("List<") and type_name.endswith(">"):
        return type_name[len("List<") : -1].strip()
    return None


def _packed_primitive(type_name: str, enums: dict) -> str | None:
    simple = type_name.split(".")[-1]
    if simple in _PRIMITIVE:
        return _PRIMITIVE[simple]
    if simple in enums:
        return enums[simple]
    return None


def _clean_float(value: float) -> float:
    rounded = round(value, 6)
    if abs(rounded - value) < 1e-5:
        return rounded
    return value
    if type_name.endswith("[]"):
        return type_name[:-2]
    if type_name.startswith("List<") and type_name.endswith(">"):
        return type_name[len("List<") : -1].strip()
    return None


def _substitute(type_name: str, generic: dict) -> str:
    if not generic:
        return type_name

    def replace(match: re.Match) -> str:
        return generic.get(match.group(0), match.group(0))

    return re.sub(r"[A-Za-z_][A-Za-z0-9_]*", replace, type_name)


def _split_generic(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip().split(".")[-1] for part in text.split(",")]


def _enum_map(enums) -> dict[str, str]:
    if not enums:
        return {}
    if isinstance(enums, dict):
        return enums
    return {name: "int" for name in enums}


def _marked_serialized(field: dict, attributes: list[str]) -> bool:
    text = " ".join(attributes)
    if "NonSerialized" in text:
        return False
    if field.get("static") or field.get("const"):
        return False
    if field.get("access") in {"public", ""}:
        return True
    return "SerializeField" in text


def _read_value(raw: bytes, offset: int, kind: str):
    if kind in {"bool", "byte"}:
        if offset >= len(raw):
            raise ValueError(kind)
        raw_byte = raw[offset]
        value = bool(raw_byte) if kind == "bool" else raw_byte
        return value, _align(offset + 1)
    if kind == "short":
        if offset + 2 > len(raw):
            raise ValueError("short")
        return struct.unpack_from("<h", raw, offset)[0], _align(offset + 2)
    if kind == "int":
        if offset + 4 > len(raw):
            raise ValueError("int")
        return struct.unpack_from("<i", raw, offset)[0], offset + 4
    if kind == "float":
        if offset + 4 > len(raw):
            raise ValueError("float")
        value = struct.unpack_from("<f", raw, offset)[0]
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("float")
        return _clean_float(value), offset + 4
    if kind == "string":
        return _read_string_value(raw, offset)
    raise ValueError(kind)


def _read_string_value(raw: bytes, offset: int):
    if offset + 4 > len(raw):
        raise ValueError("string")
    length = struct.unpack_from("<i", raw, offset)[0]
    if length < 0 or offset + 4 + length > len(raw):
        raise ValueError("string length")
    text = raw[offset + 4 : offset + 4 + length].decode("utf-8")
    return text, _align(offset + 4 + length)


def _align(offset: int) -> int:
    return (offset + 3) & ~3


def _parse_header(raw: bytes) -> tuple[str, tuple[int, int], int] | None:
    try:
        _game_object, offset = _read_pptr(raw, 0)
        _enabled, offset = _read_int(raw, offset)
        script, offset = _read_pptr(raw, offset)
        name, _start, end = _read_string(raw, offset)
    except (ValueError, UnicodeDecodeError):
        return None
    return name, script, end


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
    if length < 0 or offset + 4 + length > len(raw):
        raise ValueError("bad string length")
    text = raw[offset + 4 : offset + 4 + length].decode("utf-8")
    end = _align(offset + 4 + length)
    if end > len(raw):
        raise ValueError("truncated string padding")
    return text, offset, end
