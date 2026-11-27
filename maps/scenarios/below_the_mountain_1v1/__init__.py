"""[FA] [1v1] Below the Mountain: End's "1v1 BELOW THE MOUTAIN" layout on Coal Mountain (Steam Workshop 3846746484, 27 November 2026),
with FA conquest and a camera for each team.
End 27 Nov 2026 (#ai-ops): "modify this map to the FA standard? The zones should all be +1 zones for the new occ, add the proper occupation
game mod like in other maps, and add for both sides the starting camera location between their two respective ground spawns."
- The file has no script, so the FA conquest graft supplies it (as on End's other maps).
- End's five zones were unnamed ("Objective zone 1-5", icon 0). They are lettered in his order, 1-5 = Alpha-Echo, every zone worth 1.
- Spawns 31, 32, 34 and 36 faced 77-137 degrees away from the zones and now face them; 33 and 35 keep End's facing.
- Each team's camera is over the midpoint of its two ground spawns (the air spawn is left out).
- The map file lists DLC 3 (Coal Mountain), as coal_mountain_2v2 does."""
import uuid
import common as C
NAME='[FA] [1v1] Below the Mountain 0.1'
SKIRMISH_NAME='[FA] [1v1] Below the Mountain Skirmish 0.1'
VALUES=dict(Alpha=1,Bravo=1,Charlie=1,Delta=1,Echo=1)
# Spawns more than 45 degrees off (before): Alpha ground 31 129, 32 -77, air 36 137; Bravo ground 34 -131. Bravo 33 (-45) and air 35 (-41) keep End's facing.
TURNED={31,32,34,36}
LETTERS={f'Objective zone {i}':(n,v) for i,(n,v) in enumerate(VALUES.items(),1)}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Coal Mountain' and head['author']=='End' and meta['gameVersion'] in C.SOURCE_VERSIONS and head['dlc']==meta['dlc']==[3]
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type') in (1,18,19)],'End added a script, units or cameras. Check this merge.'
    C.strip_editor_teams(objects,meta)
    assert not [x for t in meta['teams'] for x in t['slots'] if x['lock']]
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==0,o['_dname'];o['ZoneIcon']=list(LETTERS).index(o['_dname'])+1
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    pz=[o['_uid'] for o in objects if o.get('_type')==7];assert len(pz)==1 and head['spz']==0
    head['spz']=pz[0]   # End left the active play area unset; the other FA maps name their one play area
    # End's spawns are all named GROUND or AIR, so compare by UID: the four that face more than 45 degrees from the zones are turned.
    before={o['_uid']:dict(o['rotate']) for o in objects if o.get('_type')==10}
    C.face_spawn_outliers(objects)
    assert {o['_uid'] for o in objects if o.get('_type')==10 and o['rotate']!=before[o['_uid']]}==TURNED
    C.add_team_cameras(objects,ground=True)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='End',desc=C.describe(VALUES)+' Map by End (Steam Workshop 3846746484).',prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
