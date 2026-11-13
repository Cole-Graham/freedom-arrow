"""Lateralus's Frontiers layout, with FA conquest and consistent objective symbols."""
import uuid
import common as C
NAME='[FA] [2v2] Highway of Death 0.1'
SKIRMISH_NAME='[FA] [2v2] Highway of Death Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=2,Delta=6,Echo=6,Foxtrot=3,Golf=2)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Frontiers' and meta['gameVersion']==C.GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18]
    C.strip_editor_teams(objects,meta)
    # Distinct objective IDs avoid ambiguous online map identification against Chkalovsk (31..37).
    for o in objects:
        if o.get('_type')==15:
            o['_uid']+=10000
            o['ZoneIcon']=ord(o['_dname'][0])-ord('A')+1
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    for o in objects:
        if o.get('_type')==3:
            o['players']=o['players'][:2]
    keep={x['id'] for o in objects if o.get('_type')==3 for x in o['players']}
    objects[:]=[o for o in objects if o.get('_type')!=13 or o['_uid'] in keep]
    for team in meta['teams']:team['slots']=team['slots'][:2]
    head['spz']=next(o['_uid'] for o in objects if o.get('_type')==7)
    C.face_spawns_to_objectives(objects)
    C.add_team_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
