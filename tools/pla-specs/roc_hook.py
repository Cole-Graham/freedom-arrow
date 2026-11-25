"""ROC specialization hook and reserved-ID check (Osama 25 Nov 2026 00:5x PST, thread 1575071006240931931: "create a seperate branch that is the ROC
specialization. Please reserve unit and weapon ID's so that we don't have conflicts when merging with the live build ... keep it compartmentalized").
The ROC work lives only on branch codex/batch/shawn/roc, in tools/roc/roc.py. On every other branch that file is absent and the hook adds nothing.
ROC rows take IDs from the 'roc' block in mod/id-reservations.json (g.scope). The check fails the build if any row sits in a reserved block that its
owner did not create, so live sections can never use ROC IDs. Called after every live section and the final checks; recheck runs those checks again
on the ROC rows."""
import importlib.util
from pathlib import Path
from pla_graph import reserved_owner
ROC=Path(__file__).resolve().parents[1]/'roc'/'roc.py'

def apply(t,g,ok,rec,recheck):
    if ROC.is_file():
        spec=importlib.util.spec_from_file_location('roc',ROC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with g.scope('roc'):m.apply(t,g,ok,rec)
        recheck()
    else:g.sealed=True
    held=sorted((tab,i) for tab,rows in t.items() for i in rows if reserved_owner(tab,i))
    ok(set(held)<=g.owned,('rows in reserved ID blocks that their owner did not create',sorted(set(held)-g.owned)[:20]))
    rec['reserved_ids']={'roc_loaded':ROC.is_file(),'rows':len(held)}
