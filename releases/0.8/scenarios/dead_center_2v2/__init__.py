"""[FA] [2v2] Dead Center: Lateralus's authored map with its script, built like the other authored maps (Baltiisk, Dam).
Lateralus 16 Nov 2026: "take the design of Dead Center 2v2 0.2 as is, and make it not built on the vanilla map". Until 0.2 the build
overlaid this layout onto the game's own Central Village missions; now layout.bascr is his 0.2 file (with the two build steps the
build adds again taken out: work/maps-02-20261116/dead_center_2v2_source.py). 0.1 used fixed GUIDs ...c003/c004 (retired in Runtime.cs)."""
import common as C
NAME='[FA] [2v2] Dead Center 0.2';SKIRMISH_NAME='[FA] [2v2] Dead Center Skirmish 0.2'
VALUES=dict(Alpha=4,Bravo=4,Charlie=3,Delta=3,Echo=2,Foxtrot=2,Golf=4,Hotel=4,India=4,Juliet=4)   # the native zone is spelled Juliet
LETTERS={n:(n,v) for n,v in VALUES.items()}
FLAVORS=C.authored_flavors(NAME,SKIRMISH_NAME)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),flavors=FLAVORS)
def build(game,out):C.build_authored(out,SPEC,C.prepare_authored(__file__,'Central Village',LETTERS,[f['name'] for f in FLAVORS]))
