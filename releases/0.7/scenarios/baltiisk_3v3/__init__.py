"""[FA] [3v3] Baltiisk: Lateralus's redesign of [FA] Baltiisk 0.1 (12 November 2026), with its script. It replaces the
vanilla-built Baltiisk. His Hotel and India were copies of Echo and showed "Echo"; the build labels them by name."""
import common as C
NAME='[FA] [3v3] Baltiisk 0.1';SKIRMISH_NAME='[FA] [3v3] Baltiisk Skirmish 0.1'
# Lateralus 2026-11-12.
VALUES=dict(Alpha=2,Bravo=2,Charlie=2,Delta=3,Echo=3,Foxtrot=3,Golf=3,Hotel=4,India=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
FLAVORS=C.authored_flavors(NAME,SKIRMISH_NAME)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),flavors=FLAVORS)
def build(game,out):C.build_authored(out,SPEC,C.prepare_authored(__file__,'Baltiisk',LETTERS,[f['name'] for f in FLAVORS]))
