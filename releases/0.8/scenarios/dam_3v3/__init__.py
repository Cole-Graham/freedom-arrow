"""[FA] [3v3] Dam: Lateralus's redesign of [FA] Dam 0.1 (12 November 2026), with its script. It replaces the vanilla-built Dam."""
import common as C
NAME='[FA] [3v3] Dam 0.1';SKIRMISH_NAME='[FA] [3v3] Dam Skirmish 0.1'
# Lateralus 2026-11-12. The native zone is spelled Juliet.
VALUES=dict(Alpha=3,Bravo=3,Charlie=4,Delta=4,Echo=2,Foxtrot=2,Golf=3,Hotel=3,India=4,Juliet=4,Kilo=2,Lima=2)
LETTERS={n:(n,v) for n,v in VALUES.items()}
FLAVORS=C.authored_flavors(NAME,SKIRMISH_NAME)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),flavors=FLAVORS)
def build(game,out):C.build_authored(out,SPEC,C.prepare_authored(__file__,'Dam',LETTERS,[f['name'] for f in FLAVORS]))
