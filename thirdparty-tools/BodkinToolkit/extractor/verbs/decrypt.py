"""decrypt — workdir → json/.

Scans every *.assets file in workdir for the DataBaseCompiled
MonoBehaviour (PathID 15803), decrypts its 24 field strings, and
writes one JSON (or .raw) file per table into the json/ directory.
"""
import json
import sys
from pathlib import Path

from ..game_paths import default_workdir, default_json_dir
from ..crypto import (
    FIELD_ORDER,
    aes_decrypt,
    find_databasecompiled,
    parse_databasecompiled,
)


def _find_target(work_dir: Path, UnityPy):
    """Return (env, target_obj) for the first .assets file that contains
    DataBaseCompiled, or (None, None) if none is found."""
    for assets_file in sorted(work_dir.glob("*.assets")):
        try:
            env = UnityPy.load(str(assets_file))
            target = find_databasecompiled(env)
            if target is not None:
                return env, target
        except Exception:
            continue
    return None, None


def run_decrypt(args) -> None:
    import UnityPy

    work_dir = Path(getattr(args, "work", None) or default_workdir())
    json_dir = Path(getattr(args, "json", None) or default_json_dir())

    if not work_dir.exists():
        print(f"ERR cannot find workdir at {work_dir}", file=sys.stderr)
        sys.exit(2)

    env, target = _find_target(work_dir, UnityPy)
    if target is None:
        print("ERR no asset file accepted decryption; try unpack again",
              file=sys.stderr)
        sys.exit(2)

    json_dir.mkdir(parents=True, exist_ok=True)

    try:
        parsed = parse_databasecompiled(target.get_raw_data())
        print(f"m_Name={parsed['m_Name']!r}  Level={parsed['Level']}")

        count = 0
        for f in FIELD_ORDER:
            try:
                pt = aes_decrypt(parsed["fields"][f])
            except Exception as exc:
                print(f"ERR crypto failed: {f}: {exc}", file=sys.stderr)
                sys.exit(1)

            try:
                obj = json.loads(pt.decode("utf-8"))
                out_path = json_dir / f"{f}.json"
                out_path.write_text(
                    json.dumps(obj, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                rows = len(obj) if isinstance(obj, list) else 1
                print(f"  {f:<36} rows={rows:>5}  pt={len(pt):>7}")
            except json.JSONDecodeError:
                out_path = json_dir / f"{f}.raw"
                out_path.write_bytes(pt)
                print(f"  {f:<36} non-JSON .raw  pt={len(pt):>7}")

            count += 1

        print(f"\nWrote: {json_dir}")
        print(f"Done. {count} table(s) decrypted.")

    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERR crypto failed: {exc}", file=sys.stderr)
        sys.exit(1)
