"""Lateralus's Frontiers layout, with FA conquest and consistent objective symbols."""
import uuid
import common as C
# 0.2 (Lateralus 16 Nov 2026): his zone and spawn edits (work/maps-02-20261116/merge.py); his spawn facings are kept.
NAME='[FA] [2v2] Highway of Death 0.2'
SKIRMISH_NAME='[FA] [2v2] Highway of Death Skirmish 0.2'
VALUES=dict(Alpha=2,Bravo=2,Charlie=2,Delta=6,Echo=6,Foxtrot=3,Golf=2)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Frontiers' and meta['gameVersion'] in C.SOURCE_VERSIONS
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18]
    C.strip_editor_teams(objects,meta)
    # Distinct objective IDs avoid ambiguous online map identification against Chkalovsk (31..37).
    for o in objects:
        if o.get('_type')==15:
            o['_uid']+=10000
            o['ZoneIcon']=ord(o['_dname'][0])-ord('A')+1
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    # Lateralus 14 Nov 2026: every FA map offers all 5 slots per team. The layout's 5 players and lobby slots per team stay
    # (until 0.9.0-dev.4 this build cut them to 2).
    for o in objects:
        if o.get('_type')==3 and o['_dname'] in ('Alpha team','Bravo team'):assert len(o['players'])==5,(o['_dname'],len(o['players']))
    assert all(len(t['slots'])==5 for t in meta['teams']),[len(t['slots']) for t in meta['teams']]
    head['spz']=next(o['_uid'] for o in objects if o.get('_type')==7)
    C.add_team_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
