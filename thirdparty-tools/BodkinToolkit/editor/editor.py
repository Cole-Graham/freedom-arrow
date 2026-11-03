#!/usr/bin/env python3
"""editor - standalone entry point (the tool's single front)."""
import importlib
import os
import sys

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_TOOL_DIR)
_PROJECT = os.path.basename(_ROOT_DIR)
sys.path.insert(0, os.path.join(_ROOT_DIR, "vendor"))
sys.path.insert(0, os.path.dirname(_ROOT_DIR))

_PKG = os.path.basename(_TOOL_DIR)

if __name__ == "__main__":
    importlib.import_module("%s.%s.__main__" % (_PROJECT, _PKG)).main()
