"""crypto.py — AES-256-CBC worker + MonoBehaviour binary parser.

Ported from the v2 db_crypt.py reference.  Do not call this module
directly — use the verb modules in extractor/verbs/.

Public surface:
    aes_decrypt(blob_b64: str) -> bytes
    aes_encrypt(plaintext: bytes) -> str
    parse_databasecompiled(raw: bytes) -> dict
    serialize_databasecompiled(parsed: dict) -> bytes
    find_databasecompiled(env) -> object | None
    FIELD_ORDER: list[str]
    DATABASE_COMPILED_PATH_ID: int
"""
import base64
import struct

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# ── Constants ─────────────────────────────────────────────────────────────────

AES_KEY: bytes = b"09234237536700238099172758697347"
MARKER: bytes = b"fhk3s0g3"
DATABASE_COMPILED_PATH_ID: int = 15803

FIELD_ORDER: list = [
    "Units",
    "AbilitiesJson",
    "UnitAbilitiesJson",
    "AmmunitionsJson",
    "ArmorsJson",
    "MobilityJson",
    "FlyPresetsJson",
    "UnitPropulsionsJson",
    "CountriesJson",
    "TurretsJson",
    "TurretUnitsJson",
    "WeaponsJson",
    "TurretWeaponsJson",
    "WeaponAmmunitionsJson",
    "SensorUnitsJson",
    "SensorsJson",
    "SquadMembersJson",
    "SquadWeaponsJson",
    "ModificationsJson",
    "OptionsJson",
    "UnitArmorsJson",
    "SpecializationAvailabilitiesJson",
    "SpecializationsJson",
    "TransportAvailabilitiesJson",
]

# ── AES helpers ───────────────────────────────────────────────────────────────

def aes_decrypt(blob_b64: str) -> bytes:
    """Decode and decrypt a single field value.

    Format on wire: base64( MARKER[8] + IV[16] + ciphertext )
    """
    raw = base64.b64decode(blob_b64)
    if raw[:8] != MARKER:
        raise ValueError(f"missing marker (got {raw[:8]!r})")
    cipher = AES.new(AES_KEY, AES.MODE_CBC, raw[8:24])
    return unpad(cipher.decrypt(raw[24:]), 16)


def aes_encrypt(plaintext: bytes) -> str:
    """Encrypt plaintext and return a base64-encoded wire value."""
    iv = get_random_bytes(16)
    ct = AES.new(AES_KEY, AES.MODE_CBC, iv).encrypt(pad(plaintext, 16))
    return base64.b64encode(MARKER + iv + ct).decode("ascii")


# ── Binary parser helpers ─────────────────────────────────────────────────────

def _align4(n: int) -> int:
    return (n + 3) & ~3


def _read_pptr(raw: bytes, off: int) -> tuple:
    fid = struct.unpack_from("<I", raw, off)[0]
    pid = struct.unpack_from("<q", raw, off + 4)[0]
    return (fid, pid), off + 12


def _read_int(raw: bytes, off: int) -> tuple:
    return struct.unpack_from("<i", raw, off)[0], off + 4


def _read_string(raw: bytes, off: int) -> tuple:
    ln = struct.unpack_from("<i", raw, off)[0]
    off += 4
    s = raw[off:off + ln].decode("utf-8")
    return s, _align4(off + ln)


def _write_pptr(buf: bytearray, ptr: tuple) -> None:
    buf += struct.pack("<I", ptr[0])
    buf += struct.pack("<q", ptr[1])


def _write_int(buf: bytearray, v: int) -> None:
    buf += struct.pack("<i", v)


def _write_string(buf: bytearray, s: str) -> None:
    enc = s.encode("utf-8")
    buf += struct.pack("<i", len(enc))
    buf += enc
    # 4-byte align the buffer
    remainder = len(buf) % 4
    if remainder:
        buf += b"\x00" * (4 - remainder)


# ── MonoBehaviour blob ────────────────────────────────────────────────────────

def parse_databasecompiled(raw: bytes) -> dict:
    """Deserialise raw MonoBehaviour bytes into a structured dict.

    Layout:
        m_GameObject (pptr, 12 bytes)
        m_Enabled    (int,  4 bytes)
        m_Script     (pptr, 12 bytes)
        m_Name       (length-prefixed string, 4-byte aligned)
        24 × field   (length-prefixed string, 4-byte aligned)
        Level        (int,  4 bytes)
    """
    off = 0
    go, off = _read_pptr(raw, off)
    en, off = _read_int(raw, off)
    sc, off = _read_pptr(raw, off)
    nm, off = _read_string(raw, off)
    fields: dict = {}
    for f in FIELD_ORDER:
        fields[f], off = _read_string(raw, off)
    lvl, off = _read_int(raw, off)
    if off != len(raw):
        raise ValueError(f"trailing bytes at offset {off} (total {len(raw)})")
    return {
        "m_GameObject": go,
        "m_Enabled": en,
        "m_Script": sc,
        "m_Name": nm,
        "fields": fields,
        "Level": lvl,
    }


def serialize_databasecompiled(p: dict) -> bytes:
    """Serialise a parsed dict back to raw MonoBehaviour bytes."""
    buf = bytearray()
    _write_pptr(buf, p["m_GameObject"])
    _write_int(buf, p["m_Enabled"])
    _write_pptr(buf, p["m_Script"])
    _write_string(buf, p["m_Name"])
    for f in FIELD_ORDER:
        _write_string(buf, p["fields"][f])
    _write_int(buf, p["Level"])
    return bytes(buf)


# ── UnityPy helper ────────────────────────────────────────────────────────────

def find_databasecompiled(env):
    """Return the DataBaseCompiled MonoBehaviour object from a UnityPy env, or None."""
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour" and obj.path_id == DATABASE_COMPILED_PATH_ID:
            return obj
    return None
