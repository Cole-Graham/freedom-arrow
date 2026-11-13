"""[FA] [5v5] Cold Harbor: Lateralus's Tallinn Harbour layout (13 November 2026), with FA conquest and a camera per team.
His spawn facings are kept."""
import uuid
import common as C
NAME='[FA] [5v5] Cold Harbor 0.1'
SKIRMISH_NAME='[FA] [5v5] Cold Harbor Skirmish 0.1'
# Lateralus 2026-11-13.
VALUES=dict(Alpha=3,Bravo=3,Charlie=2,Delta=2,Echo=3,Foxtrot=3,Golf=3,Hotel=3,India=2,Juliett=2)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Tallinn Harbour' and meta['gameVersion']==C.GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type') in (1,18)],'authored map has a script, units or cameras now. Check this merge.'
    C.strip_editor_teams(objects,meta)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7)
    C.add_team_cameras(objects)
    # The new cameras and look-at tags can land on 69/70/72, which the FA lobby options need.
    if C.GRAFT_UIDS&{o['_uid'] for o in objects}:C.free_uids(objects,nodes)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
