"""extractor — bundle ↔ JSON transport.

Usage:
  python -m v3.extractor <verb> [options]

Verbs:
  unpack   bundle → workdir  (extract Unity assets)
  decrypt  workdir → json/   (decrypt 24 JSON tables)
  encrypt  json/  → workdir  (re-encrypt tables into blob)
  pack     workdir → bundle  (repack; DESTRUCTIVE)

Pass '?' or '--help' after a verb for per-verb options.
"""
import sys


def _patch_question_mark():
    """Allow '?' as a help alias at the verb position."""
    if len(sys.argv) >= 2 and sys.argv[1] == "?":
        sys.argv[1] = "--help"
    elif len(sys.argv) >= 3 and sys.argv[2] == "?":
        sys.argv[2] = "--help"


def main():
    _patch_question_mark()

    import argparse
    from .verbs.unpack import run_unpack
    from .verbs.decrypt import run_decrypt
    from .verbs.encrypt import run_encrypt
    from .verbs.pack import run_pack

    p = argparse.ArgumentParser(
        prog="extractor",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="verb", metavar="verb")
    sub.required = True

    # ── unpack ────────────────────────────────────────────────────────────────
    pu = sub.add_parser("unpack", help="bundle → workdir (extract Unity assets)")
    pu.add_argument("--bundle", metavar="PATH",
                    help="path to data.unity3d (default: resolved via game_paths)")
    pu.add_argument("--work", metavar="DIR",
                    help="extraction target directory (default: v3/world/_workdir/)")
    pu.set_defaults(func=run_unpack)

    # ── decrypt ───────────────────────────────────────────────────────────────
    pd = sub.add_parser("decrypt", help="workdir → json/ (decrypt 24 JSON tables)")
    pd.add_argument("--work", metavar="DIR",
                    help="workdir source (default: v3/world/_workdir/)")
    pd.add_argument("--json", metavar="DIR",
                    help="JSON target directory (default: v3/world/json/)")
    pd.set_defaults(func=run_decrypt)

    # ── encrypt ───────────────────────────────────────────────────────────────
    pe = sub.add_parser("encrypt", help="json/ → workdir (re-encrypt tables into blob)")
    pe.add_argument("--work", metavar="DIR",
                    help="workdir (holds reference assets + output blob; default: v3/world/_workdir/)")
    pe.add_argument("--json", metavar="DIR",
                    help="JSON source directory (default: v3/world/json/)")
    pe.set_defaults(func=run_encrypt)

    # ── pack ──────────────────────────────────────────────────────────────────
    pp = sub.add_parser("pack", help="workdir → bundle (repack; DESTRUCTIVE)")
    pp.add_argument("--bundle", metavar="PATH",
                    help="path to data.unity3d (default: resolved via game_paths)")
    pp.add_argument("--work", metavar="DIR",
                    help="workdir (default: v3/world/_workdir/)")
    pp.add_argument("--yes", action="store_true",
                    help="skip overwrite confirmation")
    pp.set_defaults(func=run_pack)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
