"""pack — workdir → bundle (repack Unity bundle). DESTRUCTIVE.

Injects the re-encrypted MonoBehaviour blob produced by ``encrypt``
into the game bundle, then recompresses and atomically swaps the file
into place.

Steps:
  [1/4] Load bundle
  [2/4] Patch MonoBehaviour
  [3/4] Repack (lz4)
  [4/4] Swap into place

No bundle backup is performed here — that is ``backup``'s responsibility.
Pass ``--yes`` to skip the confirmation prompt.
"""
import io
import os
import sys
import traceback
from pathlib import Path

from ..game_paths import resolve_bundle, default_workdir
from ..crypto import find_databasecompiled

BLOB_NAME = "DataBaseCompiled.blob"
COMPRESSION = "lz4"


def run_pack(args) -> None:
    import UnityPy
    from datetime import datetime

    bundle_path = resolve_bundle(getattr(args, "bundle", None))
    work_dir = Path(getattr(args, "work", None) or default_workdir())
    skip_confirm = getattr(args, "yes", False)

    # ── Pre-flight checks ─────────────────────────────────────────────────────
    if not bundle_path.exists():
        print(f"ERR cannot find bundle at {bundle_path}", file=sys.stderr)
        sys.exit(2)

    blob_path = work_dir / BLOB_NAME
    if not blob_path.exists():
        print(
            f"ERR cannot find blob at {blob_path} — run 'encrypt' first",
            file=sys.stderr,
        )
        sys.exit(2)

    # ── Confirmation ──────────────────────────────────────────────────────────
    if not skip_confirm:
        try:
            answer = input(
                f"About to overwrite {bundle_path}. Proceed? [y/N] "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    # ── Lock check ────────────────────────────────────────────────────────────
    try:
        with open(bundle_path, "a+b"):
            pass
    except PermissionError:
        print(
            f"ERR crypto failed: '{bundle_path.name}' is locked"
            " — ensure the game is closed",
            file=sys.stderr,
        )
        sys.exit(1)

    new_blob = blob_path.read_bytes()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tmp_dir = bundle_path.parent / f".tmp_pack_{ts}"

    try:
        # [1/4] Load ──────────────────────────────────────────────────────────
        print(f"[1/4] Loading bundle {bundle_path.name} ...")
        # Load from an in-memory copy so UnityPy keeps no OS handle on the
        # bundle file. Otherwise the [4/4] os.replace swap fails on Windows
        # ("file in use"). No backup is made here, by design (see 'backup').
        env = UnityPy.load(io.BytesIO(bundle_path.read_bytes()))

        target = find_databasecompiled(env)
        if target is None:
            print(
                "ERR no asset file accepted decryption; try unpack again",
                file=sys.stderr,
            )
            sys.exit(2)

        # [2/4] Patch ─────────────────────────────────────────────────────────
        print("[2/4] Patching MonoBehaviour ...")
        target.set_raw_data(new_blob)

        # [3/4] Repack ────────────────────────────────────────────────────────
        tmp_dir.mkdir(exist_ok=False)
        print(f"[3/4] Saving repacked bundle (compression={COMPRESSION}) ...")
        env.save(pack=COMPRESSION, out_path=str(tmp_dir))

        written = list(tmp_dir.iterdir())
        if not written:
            raise RuntimeError("UnityPy.save produced no output files")

        # UnityPy may name the output file differently; prefer matching name.
        produced = tmp_dir / bundle_path.name
        if not produced.exists():
            produced = written[0]

        # [4/4] Swap ──────────────────────────────────────────────────────────
        print("[4/4] Swapping into place ...")
        os.replace(produced, bundle_path)
        print(f"Done. Patched bundle at {bundle_path}")

    except SystemExit:
        raise
    except Exception as exc:
        traceback.print_exc(file=sys.stderr) 
        print(f"ERR crypto failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temp dir whether we succeeded or not.
        try:
            if tmp_dir.exists():
                for f in tmp_dir.iterdir():
                    f.unlink()
                tmp_dir.rmdir()
        except Exception:
            pass
