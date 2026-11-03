"""link verbs."""
from . import show, touch, init, walk

VERBS = {"show": show, "touch": touch, "init": init, "walk": walk}
__all__ = ["VERBS"]
