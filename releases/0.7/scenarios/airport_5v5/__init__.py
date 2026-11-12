"""[FA] [5v5] Airport: Lateralus's redesign of [FA] Airport 0.1 (12 November 2026), with its script. It replaces the vanilla
Airport entry. Lateralus put spawns outside Play Zone Small, so the build removes the lobby Size option and its player-count
logic: Play Zone Large (the whole 9000 x 9000 map) is always the play area."""
import common as C
NAME='[FA] [5v5] Airport 0.1';SKIRMISH_NAME='[FA] [5v5] Airport Skirmish 0.1'
# Lateralus 2026-11-12.
VALUES=dict(Alpha=3,Bravo=2,Charlie=2,Delta=3,Echo=2,Foxtrot=2,Golf=2,Hotel=4,India=2,Juliett=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
LARGE,SMALL,SIZE_OPTION=10,55,53
# The native size logic. Large (or Auto with 9+ players) starts conquest node 330. Medium hid Golf and India (native uids 40
# and 46, nodes 223 225); Small showed Foxtrot and Hotel, hid Golf and India (228 229) and selected Play Zone Small. Lateralus
# removed zones 40 and 46, so 223 225 228 229 had no target: the editor's "missing any target".
SIZE_NODES={22:'getPblInt',34:'subgraph',35:'subgraphEnter',36:'subgraphExit',187:'getPblEnum',196:'compare3',197:'compare3',
            198:'compare3',210:'compare3',223:'objVisible2',225:'objVisible2',228:'objVisible2',229:'objVisible2',
            231:'objVisible2',232:'objVisible2',239:'act_pz',245:'Network Players',248:'Network Players',249:'calc3',
            253:'compare3',257:'compare3',264:'delay',265:'delay',337:'setConquestMode',194:'comment',195:'comment',
            209:'comment',216:'comment',261:'comment',262:'comment',263:'note'}
MATCH_CHECK,CONQUEST=69696,330
def remove_size_logic(head,nodes,objects,meta):
    byid={b['id']:b for b in nodes['b']}
    assert {i:byid[i]['nnKey'] for i in SIZE_NODES if i in byid}==SIZE_NODES,'size logic changed. Check this merge.'
    nodes['b']=[b for b in nodes['b'] if b['id'] not in SIZE_NODES]
    nodes['c']=[c for c in nodes['c'] if c['a'] not in SIZE_NODES and c['b'] not in SIZE_NODES]
    nodes['c'].append(dict(a=CONQUEST,b=MATCH_CHECK,c='in2',d='FFalse',e=MATCH_CHECK))
    assert head['spz']==LARGE
    gone={SMALL,SIZE_OPTION}
    assert {o['_dname'] for o in objects if o['_uid'] in gone}=={'Play Zone Small','ui_lobby_Size_Title'}
    objects[:]=[o for o in objects if o['_uid'] not in gone]
    meta['pblOpt']=[p for p in meta['pblOpt'] if p['id']!=SIZE_OPTION]
    text=C.dump(nodes).decode()+C.dump(objects).decode()
    assert not [g for g in gone if f'"c{g}"' in text or f'"id": {g},' in text],'a removed object is still referenced'
    assert not {b['nnKey'] for b in nodes['b']}&{'objVisible2','act_pz','Network Players'}
    assert [o['_uid'] for o in objects if o.get('_type')==7]==[LARGE]
FLAVORS=C.authored_flavors(NAME,SKIRMISH_NAME)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),flavors=FLAVORS)
def build(game,out):
    C.build_authored(out,SPEC,C.prepare_authored(__file__,'Airport',LETTERS,[f['name'] for f in FLAVORS],remove_size_logic))
