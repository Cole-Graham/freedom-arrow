#!/usr/bin/env python3
"""import_pipeline — standalone entry point. Chains tools via their fronts."""
import importlib, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))   # toolkit folder
_PROJECT = os.path.basename(_ROOT)
sys.path.insert(0, os.path.join(_ROOT, "vendor"))
sys.path.insert(0, os.path.dirname(_ROOT))
_P = os.path.basename(_HERE)
importlib.import_module("%s.actions.%s.run" % (_PROJECT, _P)).main()
