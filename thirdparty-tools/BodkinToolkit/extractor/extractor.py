#!/usr/bin/env python3
"""extractor — standalone entry point (the tool's single front).

Package name is derived from the toolkit folder, so the toolkit works no
matter what the folder is named (must be a valid Python identifier).
Shim only: make the project self-contained, then run the package `__main__`.
"""
import importlib
import os
import sys

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_TOOL_DIR)          # the toolkit folder
_PROJECT = os.path.basename(_ROOT_DIR)          # e.g. "Bodkin"
sys.path.insert(0, os.path.join(_ROOT_DIR, "vendor"))   # bundled deps
sys.path.insert(0, os.path.dirname(_ROOT_DIR))          # parent -> import `<project>`

_PKG = os.path.basename(_TOOL_DIR)

if __name__ == "__main__":
    importlib.import_module("%s.%s.__main__" % (_PROJECT, _PKG)).main()
