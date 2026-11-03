"""Parse and splice a DataBaseCompiled MonoBehaviour.

An empty edit returns the original bytes. A dirty field is re-encoded in
place; every other byte of the object, including untouched ciphertext, stays.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from pipeline.crypto import has_marker
from pipeline.tables import FIELD_ORDER, OBJECT_NAME


@dataclass(frozen=True)
class DatabaseBlob:
    raw: bytes
    prefix: bytes
    fields: dict[str, str]
    spans: dict[str, tuple[int, int]]
    trailer: bytes
    script: tuple[int, int] | None
    game_object: tuple[int, int] | None
    enabled: int | None
    level: int | None

    @property
    def name(self) -> str:
        return OBJECT_NAME


def parse_database(raw: bytes) -> DatabaseBlob:
    """Parse raw MonoBehaviour bytes. The object name is DataBaseCompiled."""
    parsed = _parse_at(raw, 0)
    if parsed is not None:
        return parsed

    needle = struct.pack("<i", len(OBJECT_NAME)) + OBJECT_NAME.encode("utf-8")
    start = 0
    while True:
        found = raw.find(needle, start)
        if found < 0:
            break
        parsed = _parse_fields_from_name(raw, found)
        if parsed is not None:
            return parsed
        start = found + 1
    raise ValueError(f"{OBJECT_NAME} not found in MonoBehaviour ({len(raw)} bytes)")


def rebuild(blob: DatabaseBlob, fields: dict[str, str]) -> bytes:
    """Return object bytes with `fields` substituted.

    When every field string is unchanged, the original buffer is returned.
    """
    if all(fields[name] == blob.fields[name] for name in FIELD_ORDER):
        return blob.raw

    buf = bytearray(blob.prefix)
    for name in FIELD_ORDER:
        value = fields[name]
        start, end = blob.spans[name]
        if value == blob.fields[name] and len(buf) == start:
            buf += blob.raw[start:end]
        else:
            _write_string(buf, value)
    buf += blob.trailer
    return bytes(buf)


def _parse_at(raw: bytes, offset: int) -> DatabaseBlob | None:
    try:
        game_object, offset = _read_pptr(raw, offset)
        enabled, offset = _read_int(raw, offset)
        script, offset = _read_pptr(raw, offset)
        name, _name_start, offset = _read_string(raw, offset)
    except ValueError:
        return None
    if name != OBJECT_NAME:
        return None
    return _read_fields(raw, offset, script, game_object, enabled)


def _parse_fields_from_name(raw: bytes, name_at: int) -> DatabaseBlob | None:
    try:
        name, _start, offset = _read_string(raw, name_at)
    except ValueError:
        return None
    if name != OBJECT_NAME:
        return None
    script = game_object = None
    enabled = None
    if name_at >= 28:
        try:
            game_object, cursor = _read_pptr(raw, name_at - 28)
            enabled, cursor = _read_int(raw, cursor)
            script, cursor = _read_pptr(raw, cursor)
            if cursor != name_at:
                script = game_object = None
                enabled = None
        except ValueError:
            script = game_object = None
            enabled = None
    return _read_fields(raw, offset, script, game_object, enabled)


def _read_fields(
    raw: bytes,
    offset: int,
    script: tuple[int, int] | None,
    game_object: tuple[int, int] | None,
    enabled: int | None,
) -> DatabaseBlob | None:
    """Read the 24 encrypted fields.

    Unity 6 inserts an empty string between m_Name and the tables. That string
    stays in the prefix so an unchanged object round-trips byte for byte.
    """
    try:
        markers: list[tuple[str, int, int]] = []
        while len(markers) < len(FIELD_ORDER):
            value, start, end = _read_string(raw, offset)
            offset = end
            if has_marker(value):
                markers.append((value, start, end))
                continue
            if markers:
                return None
        fields = {name: markers[index][0] for index, name in enumerate(FIELD_ORDER)}
        spans = {name: (markers[index][1], markers[index][2]) for index, name in enumerate(FIELD_ORDER)}
    except ValueError:
        return None
    trailer = raw[markers[-1][2] :]
    level = struct.unpack_from("<i", trailer, 0)[0] if len(trailer) >= 4 else None
    return DatabaseBlob(
        raw=raw,
        prefix=raw[: markers[0][1]],
        fields=fields,
        spans=spans,
        trailer=trailer,
        script=script,
        game_object=game_object,
        enabled=enabled,
        level=level,
    )


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
    start = offset
    text = raw[offset + 4 : offset + 4 + length].decode("utf-8")
    end = (offset + 4 + length + 3) & ~3
    if end > len(raw):
        raise ValueError("truncated string padding")
    return text, start, end


def _write_string(buf: bytearray, text: str) -> None:
    encoded = text.encode("utf-8")
    buf += struct.pack("<i", len(encoded))
    buf += encoded
    remainder = len(buf) % 4
    if remainder:
        buf += b"\x00" * (4 - remainder)
