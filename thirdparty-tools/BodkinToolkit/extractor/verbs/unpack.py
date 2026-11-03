"""unpack — bundle → workdir.

Extracts resources.assets (and globalgamemanagers.assets) from the
Unity bundle into the workdir for subsequent decrypt/encrypt steps.
"""
import sys
from pathlib import Path

from ..game_paths import resolve_bundle, default_workdir

# Inner-file names worth extracting from the bundle.
_EXTRACT = {"resources.assets", "globalgamemanagers.assets"}


def run_unpack(args) -> None:
    import UnityPy

    bundle_path = resolve_bundle(getattr(args, "bundle", None))
    work_dir = Path(getattr(args, "work", None) or default_workdir())

    if not bundle_path.exists():
        print(f"ERR cannot find bundle at {bundle_path}", file=sys.stderr)
        sys.exit(2)

    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"Loading {bundle_path.name} ...")

    try:
        env = UnityPy.load(str(bundle_path))
        bundle = env.file
        n = 0
        for name, inner in bundle.files.items():
            # Strip any cabinet prefix (e.g. "CAB-xxxx/resources.assets")
            base = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if base in _EXTRACT:
                data = inner.save()
                out_path = work_dir / base
                out_path.write_bytes(data)
                print(f"  extracted {base} ({len(data):,} bytes)")
                n += 1

        if n == 0:
            print("  bundle contains:", file=sys.stderr)
            for name in bundle.files:
                print(f"    - {name}", file=sys.stderr)
            print("ERR no asset file accepted decryption; try unpack again",
                  file=sys.stderr)
            sys.exit(2)

        print(f"Done. {n} file(s) -> {work_dir}")

    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERR crypto failed: {exc}", file=sys.stderr)
        sys.exit(1)
