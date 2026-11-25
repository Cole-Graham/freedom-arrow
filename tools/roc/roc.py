"""ROC specialization data (Osama 25 Nov 2026 00:5x PST, thread 1575071006240931931; details from Shawn1989 in that thread).
Runs only on branch codex/batch/shawn/roc, last in the batch (tools/pla-specs/roc_hook.py), inside g.scope('roc').
Make every new row with g.add(table, row_to_copy, fields): it takes the next free ID in the ROC block of mod/id-reservations.json.
g.put(table, max(U)+1, ...) fails here on purpose. Editing an existing live row is allowed, but list it in rec['roc']['live_edits']."""

def apply(t,g,ok,rec):
    rec['roc']={'cards':{},'live_edits':[]}
