"""import verbs. Each exposes configure(parser) and run(args)."""
from . import json as json_verb
from . import one as one_verb

VERBS = {"json": json_verb, "one": one_verb}
__all__ = ["VERBS"]
