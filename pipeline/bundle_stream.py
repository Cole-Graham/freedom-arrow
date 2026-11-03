"""Read and rewrite data.unity3d without holding the whole archive in memory.

UnityPy loads every decompressed block at once. This bundle expands to about
14 GB, which does not fit. Each serialized file is under 1 GB, so discovery
extracts one assets file at a time and inject rebuilds the archive from a stream.
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from pathlib import Path

from UnityPy.enums import CompressionFlags
from UnityPy.helpers.CompressionHelper import (
    COMPRESSION_MAP,
    DECOMPRESSION_MAP,
)

from pipeline.errors import PipelineError

_LZ4 = 2
_CHUNK = 0x20000
# Directory info is combined with block info, block info sits at the end,
# and file data is LZ4. This is the layout UnityPy writes for pack="lz4".
_DATA_FLAG = 0x80 | 0x40 | _LZ4


@dataclass(frozen=True)
class Block:
    uncompressed_size: int
    compressed_size: int
    flags: int
    compressed_offset: int


@dataclass(frozen=True)
class BundleEntry:
    name: str
    offset: int
    size: int
    flags: int


@dataclass(frozen=True)
class BundleIndex:
    path: Path
    format_version: int
    version_player: str
    version_engine: str
    blocks: tuple[Block, ...]
    files: tuple[BundleEntry, ...]


def read_index(path: Path) -> BundleIndex:
    with path.open("rb") as handle:
        signature = _read_cstring(handle)
        if signature != "UnityFS":
            raise PipelineError(f"{path} is not a UnityFS bundle")
        format_version = _read_uint(handle)
        version_player = _read_cstring(handle)
        version_engine = _read_cstring(handle)
        _bundle_size = _read_long(handle)
        compressed_info = _read_uint(handle)
        uncompressed_info = _read_uint(handle)
        data_flag = _read_uint(handle)
        if format_version >= 7:
            _align(handle, 16)
        info_start = handle.tell()
        if data_flag & 0x80:
            handle.seek(0, 2)
            handle.seek(handle.tell() - compressed_info)
        info = _decompress_flag(handle.read(compressed_info), uncompressed_info, data_flag)
        if data_flag & 0x80:
            data_start = info_start
        else:
            handle.seek(info_start + compressed_info)
            if data_flag & 0x200:
                _align(handle, 16)
            data_start = handle.tell()

    blocks, files = _parse_info(info, data_start)
    return BundleIndex(
        path=path,
        format_version=format_version,
        version_player=version_player,
        version_engine=version_engine,
        blocks=blocks,
        files=files,
    )


def extract_file(index: BundleIndex, name: str) -> bytes:
    entry = _entry(index, name)
    out = bytearray()
    end = entry.offset + entry.size
    position = 0
    for block in index.blocks:
        block_end = position + block.uncompressed_size
        if block_end > entry.offset and position < end:
            data = _read_block(index, block)
            local_start = max(0, entry.offset - position)
            local_end = min(len(data), end - position)
            out += data[local_start:local_end]
        position = block_end
    if len(out) != entry.size:
        raise PipelineError(f"extracted {len(out)} bytes of {name}, expected {entry.size}")
    return bytes(out)


def scan_assets(index: BundleIndex, on_file) -> None:
    """Decompress once. `on_file(name, data) -> True` stops the scan.

    Only `*.assets` files are buffered. Resource streams are skipped in place.
    """
    files = index.files
    file_index = 0
    filled = 0
    buffer = bytearray()
    position = 0
    seen = 0
    for block in index.blocks:
        data = _read_block(index, block)
        local = 0
        while local < len(data) and file_index < len(files):
            entry = files[file_index]
            cursor = position + local
            if cursor < entry.offset:
                local += min(entry.offset - cursor, len(data) - local)
                continue
            want = entry.name.endswith(".assets")
            need = entry.size - filled
            take = min(need, len(data) - local)
            if want:
                buffer += data[local : local + take]
            filled += take
            local += take
            if filled == entry.size:
                if want:
                    seen += 1
                    print(f"  scanned {entry.name} ({entry.size:,} bytes)", flush=True)
                    if on_file(entry.name, bytes(buffer)):
                        return
                    buffer.clear()
                filled = 0
                file_index += 1
        position += len(data)
        del data
    if file_index != len(files):
        raise PipelineError(
            f"bundle scan ended early at file {file_index} of {len(files)} after {seen} assets"
        )


def pack_files(destination: Path, files: dict[str, bytes]) -> BundleIndex:
    """Write a new LZ4 UnityFS bundle containing exactly `files`, in dict order."""
    entries: list[BundleEntry] = []
    offset = 0
    pieces: list[bytes] = []
    for name, data in files.items():
        entries.append(BundleEntry(name, offset, len(data), 0))
        pieces.append(data)
        offset += len(data)
    header = BundleIndex(
        path=destination,
        format_version=8,
        version_player="5.x.x",
        version_engine="6000.3.24f1",
        blocks=(),
        files=tuple(entries),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    compressed_blocks = destination.with_suffix(destination.suffix + ".blocks")
    try:
        block_info = _compress_chunks(_iter_pieces(pieces), compressed_blocks)
        _assemble(header, entries, block_info, compressed_blocks, destination)
    finally:
        if compressed_blocks.exists():
            compressed_blocks.unlink()
    return read_index(destination)


def write_bundle(index: BundleIndex, destination: Path, replacements: dict[str, bytes]) -> None:
    """Write a UnityFS bundle, substituting `replacements` by file name."""
    unknown = set(replacements) - {entry.name for entry in index.files}
    if unknown:
        raise PipelineError(f"replacement names are not in the bundle: {sorted(unknown)}")

    new_files: list[BundleEntry] = []
    offset = 0
    for entry in index.files:
        size = len(replacements[entry.name]) if entry.name in replacements else entry.size
        new_files.append(BundleEntry(entry.name, offset, size, entry.flags))
        offset += size

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    compressed_blocks = partial.with_suffix(partial.suffix + ".blocks")
    try:
        block_info = _compress_payload(index, replacements, compressed_blocks)
        _assemble(index, new_files, block_info, compressed_blocks, partial)
        partial.replace(destination)
    finally:
        if compressed_blocks.exists():
            compressed_blocks.unlink()
        if partial.exists() and partial != destination:
            # replace() removes partial on success; a failed assemble may leave it
            if partial.exists():
                partial.unlink()


def _compress_payload(index: BundleIndex, replacements: dict[str, bytes], dest: Path) -> list[tuple[int, int, int]]:
    return _compress_chunks(_iter_output(index, replacements), dest, progress=True)


def _iter_pieces(pieces: list[bytes]):
    step = 1024 * 1024
    for piece in pieces:
        view = memoryview(piece)
        for start in range(0, len(view), step):
            yield bytes(view[start : start + step])


def _compress_chunks(pieces, dest: Path, progress: bool = False) -> list[tuple[int, int, int]]:
    block_info: list[tuple[int, int, int]] = []
    pending = bytearray()
    written = 0

    def emit(chunk: bytes) -> None:
        compressed = COMPRESSION_MAP[CompressionFlags.LZ4](chunk)
        with dest.open("ab") as handle:
            if len(compressed) >= len(chunk):
                handle.write(chunk)
                block_info.append((len(chunk), len(chunk), 0))
            else:
                handle.write(compressed)
                block_info.append((len(chunk), len(compressed), _LZ4))

    if dest.exists():
        dest.unlink()
    for piece in pieces:
        pending += piece
        while len(pending) >= _CHUNK:
            emit(bytes(pending[:_CHUNK]))
            del pending[:_CHUNK]
            written += _CHUNK
            if progress and written % (512 * 1024 * 1024) == 0:
                print(f"  compressed {written / 1024**3:.1f} GB", flush=True)
    if pending:
        emit(bytes(pending))
    return block_info


def _iter_output(index: BundleIndex, replacements: dict[str, bytes]):
    intervals = [
        (entry.offset, entry.size, replacements[entry.name])
        for entry in index.files
        if entry.name in replacements
    ]
    interval_index = 0
    source_pos = 0
    skip = 0
    for block in index.blocks:
        data = _read_block(index, block)
        local = 0
        while local < len(data) or (
            skip == 0 and interval_index < len(intervals) and source_pos == intervals[interval_index][0]
        ):
            if skip:
                if local >= len(data):
                    break
                drop = min(skip, len(data) - local)
                skip -= drop
                local += drop
                source_pos += drop
                continue
            if local >= len(data) and not (
                interval_index < len(intervals) and source_pos == intervals[interval_index][0]
            ):
                break
            if interval_index < len(intervals) and source_pos == intervals[interval_index][0]:
                _offset, old_size, new_bytes = intervals[interval_index]
                interval_index += 1
                skip = old_size
                view = memoryview(new_bytes)
                step = 1024 * 1024
                for start in range(0, len(view), step):
                    yield bytes(view[start : start + step])
                continue
            if local >= len(data):
                break
            if interval_index < len(intervals) and source_pos < intervals[interval_index][0]:
                room = intervals[interval_index][0] - source_pos
                take = min(room, len(data) - local)
            else:
                take = len(data) - local
            yield data[local : local + take]
            local += take
            source_pos += take
        del data


def _assemble(
    index: BundleIndex,
    files: list[BundleEntry],
    block_info: list[tuple[int, int, int]],
    compressed_blocks: Path,
    destination: Path,
) -> None:
    info = _directory_bytes(files, block_info)
    compressed_info = COMPRESSION_MAP[CompressionFlags.LZ4](info)
    prefix = bytearray()
    prefix += b"UnityFS\x00"
    prefix += struct.pack(">I", index.format_version)
    prefix += index.version_player.encode("utf-8") + b"\x00"
    prefix += index.version_engine.encode("utf-8") + b"\x00"
    size_at = len(prefix)
    prefix += struct.pack(">q", 0)
    prefix += struct.pack(">I", len(compressed_info))
    prefix += struct.pack(">I", len(info))
    prefix += struct.pack(">I", _DATA_FLAG)
    if index.format_version >= 7:
        pad = (16 - (len(prefix) % 16)) % 16
        prefix += b"\x00" * pad

    with destination.open("wb") as handle:
        handle.write(prefix)
        with compressed_blocks.open("rb") as blocks:
            while True:
                chunk = blocks.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        handle.write(compressed_info)
        total = handle.tell()
        handle.seek(size_at)
        handle.write(struct.pack(">q", total))


def _directory_bytes(files: list[BundleEntry], block_info: list[tuple[int, int, int]]) -> bytes:
    out = bytearray(b"\x00" * 16)
    out += struct.pack(">i", len(block_info))
    for uncompressed, compressed, flag in block_info:
        out += struct.pack(">IIH", uncompressed, compressed, flag)
    out += struct.pack(">i", len(files))
    for entry in files:
        out += struct.pack(">q", entry.offset)
        out += struct.pack(">q", entry.size)
        out += struct.pack(">I", entry.flags)
        out += entry.name.encode("utf-8") + b"\x00"
    return bytes(out)


def _parse_info(info: bytes, data_start: int) -> tuple[tuple[Block, ...], tuple[BundleEntry, ...]]:
    offset = 16
    count = struct.unpack_from(">i", info, offset)[0]
    offset += 4
    compressed_at = data_start
    blocks: list[Block] = []
    for _ in range(count):
        uncompressed, compressed, flag = struct.unpack_from(">IIH", info, offset)
        offset += 10
        blocks.append(Block(uncompressed, compressed, flag, compressed_at))
        compressed_at += compressed
    file_count = struct.unpack_from(">i", info, offset)[0]
    offset += 4
    files: list[BundleEntry] = []
    for _ in range(file_count):
        file_offset, size, flags = struct.unpack_from(">qqI", info, offset)
        offset += 20
        end = info.index(b"\x00", offset)
        name = info[offset:end].decode("utf-8")
        offset = end + 1
        files.append(BundleEntry(name, file_offset, size, flags))
    return tuple(blocks), tuple(files)


def _read_block(index: BundleIndex, block: Block) -> bytes:
    with index.path.open("rb") as handle:
        handle.seek(block.compressed_offset)
        compressed = handle.read(block.compressed_size)
    if len(compressed) != block.compressed_size:
        raise PipelineError(f"short read in {index.path.name}")
    return _decompress_flag(compressed, block.uncompressed_size, block.flags)


def _decompress_flag(compressed: bytes, uncompressed_size: int, flags: int) -> bytes:
    kind = CompressionFlags(flags & 0x3F)
    if kind == CompressionFlags.NONE:
        return compressed
    if kind not in DECOMPRESSION_MAP:
        raise PipelineError(f"unsupported bundle compression {kind!r}")
    return DECOMPRESSION_MAP[kind](compressed, uncompressed_size)


def _entry(index: BundleIndex, name: str) -> BundleEntry:
    for entry in index.files:
        if entry.name == name:
            return entry
    raise PipelineError(f"{name} is not in {index.path.name}")


def _read_cstring(handle) -> str:
    chars = bytearray()
    while True:
        byte = handle.read(1)
        if byte in (b"", b"\x00"):
            break
        chars += byte
    return chars.decode("utf-8")


def _read_uint(handle) -> int:
    return struct.unpack(">I", handle.read(4))[0]


def _read_long(handle) -> int:
    return struct.unpack(">q", handle.read(8))[0]


def _align(handle, alignment: int) -> None:
    position = handle.tell()
    handle.seek(position + (alignment - position % alignment) % alignment)


def load_bytes(data: bytes):
    try:
        import UnityPy
    except ImportError as exc:
        raise PipelineError(
            "UnityPy is not installed. From the repo root: pip install -r pipeline/requirements.txt"
        ) from exc
    return UnityPy.load(io.BytesIO(data))
