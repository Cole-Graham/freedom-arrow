"""[FA] [5v5] Airport: Lateralus's redesign of [FA] Airport 0.1 (12 November 2026), with its script. It replaces the vanilla
Airport entry. Play Zone Large (the whole 9000 x 9000 map) is always the play area.
0.2 (Lateralus 14 Nov 2026): zone sizes and positions adjusted. His 0.2 export already has no lobby Size option, no Play Zone
Small and no player-count logic (0.1 had them and this build removed them), so the build only checks that they stay gone."""
import common as C
NAME='[FA] [5v5] Airport 0.2';SKIRMISH_NAME='[FA] [5v5] Airport Skirmish 0.2'
# Lateralus 2026-11-12; unchanged in 0.2.
VALUES=dict(Alpha=3,Bravo=2,Charlie=2,Delta=3,Echo=2,Foxtrot=2,Golf=2,Hotel=4,India=2,Juliett=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
LARGE=10
def no_size_logic(head,nodes,objects,meta):
    assert not {b['nnKey'] for b in nodes['b']}&{'objVisible2','act_pz','Network Players'},'size logic is back. Check this merge.'
    assert head['spz']==LARGE and [o['_uid'] for o in objects if o.get('_type')==7]==[LARGE]
    assert not {o['_dname'] for o in objects}&{'Play Zone Small','ui_lobby_Size_Title'}
    assert [p['id'] for p in meta['pblOpt']]==[48,49,51,56],meta['pblOpt']
FLAVORS=C.authored_flavors(NAME,SKIRMISH_NAME)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),flavors=FLAVORS)
def build(game,out):
    C.build_authored(out,SPEC,C.prepare_authored(__file__,'Airport',LETTERS,[f['name'] for f in FLAVORS],no_size_logic))
