"""export verbs."""
from . import run as run_verb
from . import one as one_verb

VERBS = {"run": run_verb, "one": one_verb}
__all__ = ["VERBS"]
