"""encrypt — json/ → workdir (re-encrypted MonoBehaviour blob).

Reads JSON (or .raw) table files from json_dir, re-encrypts each field,
serialises a new MonoBehaviour binary blob, and writes it to:

    <workdir>/DataBaseCompiled.blob

The blob name is fixed so that ``pack`` can locate it without configuration.

The workdir must already contain resources.assets (produced by ``unpack``)
so that the non-field header data (m_GameObject, m_Enabled, m_Script,
m_Name, Level) can be read as a reference.
"""
import json
import sys
from pathlib import Path

from ..game_paths import default_workdir, default_json_dir
from ..crypto import (
    FIELD_ORDER,
    aes_encrypt,
    find_databasecompiled,
    parse_databasecompiled,
    serialize_databasecompiled,
)

BLOB_NAME = "DataBaseCompiled.blob"


def _find_reference(work_dir: Path, UnityPy):
    """Return the parsed DataBaseCompiled dict from the first matching .assets."""
    for assets_file in sorted(work_dir.glob("*.assets")):
        try:
            env = UnityPy.load(str(assets_file))
            target = find_databasecompiled(env)
            if target is not None:
                return parse_databasecompiled(target.get_raw_data()), len(target.get_raw_data())
        except Exception:
            continue
    return None, 0


def run_encrypt(args) -> None:
    import UnityPy

    work_dir = Path(getattr(args, "work", None) or default_workdir())
    json_dir = Path(getattr(args, "json", None) or default_json_dir())

    if not work_dir.exists():
        print(f"ERR cannot find workdir at {work_dir}", file=sys.stderr)
        sys.exit(2)

    parsed, old_blob_size = _find_reference(work_dir, UnityPy)
    if parsed is None:
        print("ERR no asset file accepted decryption; try unpack again",
              file=sys.stderr)
        sys.exit(2)

    try:
        changed = []
        for f in FIELD_ORDER:
            jp = json_dir / f"{f}.json"
            rp = json_dir / f"{f}.raw"
            if jp.exists():
                obj = json.loads(jp.read_text(encoding="utf-8"))
                pt = json.dumps(
                    obj, separators=(",", ":"), ensure_ascii=False
                ).encode("utf-8")
                parsed["fields"][f] = aes_encrypt(pt)
                changed.append(f)
            elif rp.exists():
                parsed["fields"][f] = aes_encrypt(rp.read_bytes())
                changed.append(f)

        new_blob = serialize_databasecompiled(parsed)
        blob_path = work_dir / BLOB_NAME
        blob_path.write_bytes(new_blob)

        delta = len(new_blob) - old_blob_size
        print(f"  re-encrypted {len(changed)}: {', '.join(changed)}")
        print(f"  blob: {old_blob_size:,} -> {len(new_blob):,} ({delta:+,})")
        print(f"Done. {len(changed)} table(s) encrypted -> {blob_path}")

    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERR crypto failed: {exc}", file=sys.stderr)
        sys.exit(1)
