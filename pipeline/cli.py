"""Command line for the data pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.channels import parse_channel
from pipeline.commands import apply, decrypt, discover, hangar, il2cpp, inject, rebase_command, survey, update
from pipeline.package import package
from pipeline.config import load_config
from pipeline.errors import PipelineError, RebaseConflictError


def _channel_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--channel",
        default="stable",
        choices=("stable", "testing"),
        help="stable uses mod/constants; testing uses mod/testing/constants (default: stable)",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument(
        "--config",
        type=Path,
        help="config file (default: config.YAML next to config.template.YAML)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("discover", help="find DataBaseCompiled by name and record the build")
    commands.add_parser("decrypt", help="write the 24 JSON tables and their original ciphertext")
    commands.add_parser(
        "survey",
        help="catalog cover, forest, and suppression data into cache/survey",
    )
    commands.add_parser(
        "il2cpp",
        help="dump cover config types from GameAssembly into cache/il2cpp",
    )
    apply_parser = commands.add_parser("apply", help="merge channel constants onto the vanilla snapshot")
    _channel_argument(apply_parser)
    inject_parser = commands.add_parser("inject", help="write dist/<channel>/data.unity3d")
    _channel_argument(inject_parser)
    package_parser = commands.add_parser("package", help="write a .bamod modpack for BAModLauncher")
    _channel_argument(package_parser)
    commands.add_parser("hangar", help="swap the stable bundle in, launch, then restore")

    rebase_parser = commands.add_parser("rebase", help="merge constants onto a new vanilla snapshot")
    _channel_argument(rebase_parser)
    rebase_parser.add_argument(
        "--accept",
        action="store_true",
        help="keep constants after reviewing conflicts and move the manifest forward",
    )
    update_parser = commands.add_parser("update", help="decrypt, rebase, apply, and inject")
    _channel_argument(update_parser)
    update_parser.add_argument(
        "--accept",
        action="store_true",
        help="keep constants after reviewing conflicts and move the manifest forward",
    )

    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "discover":
            discover(cfg)
        elif args.command == "decrypt":
            decrypt(cfg)
        elif args.command == "survey":
            survey(cfg)
        elif args.command == "il2cpp":
            il2cpp(cfg)
        elif args.command == "apply":
            apply(cfg, parse_channel(args.channel))
        elif args.command == "inject":
            inject(cfg, parse_channel(args.channel))
        elif args.command == "package":
            package(cfg, parse_channel(args.channel))
        elif args.command == "rebase":
            rebase_command(cfg, accept=args.accept, channel=parse_channel(args.channel))
        elif args.command == "update":
            update(cfg, accept=args.accept, channel=parse_channel(args.channel))
        elif args.command == "hangar":
            return hangar(cfg)
        else:
            parser.error(f"unknown command {args.command}")
    except RebaseConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
