"""backup verbs."""
from . import make, restore, list as list_verb, diff

VERBS = {"make": make, "restore": restore, "list": list_verb, "diff": diff}
__all__ = ["VERBS"]
