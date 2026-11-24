"""[FA] [2v2] Coal Mountain: Lateralus's Coal Mountain layout (23 November 2026, FA_2v2_Coal_Mountain_0.1.zip in thread
1572962048705429598), with FA conquest and a camera per team.
Lateralus 23 Nov 2026: "add this map to the mod, remove the humvees and waypoints ... A B - 2 points, C - 3 points, D E F G - 4 points".
- His eight test Humvees and their three waypoints are removed.
- Bravo's Spawn point 9 faced 50 degrees away from the zones (west); it now faces them. His other facings (2-29 degrees off) are kept.
- The map needs the game's DLC 3, as Kadaga and Oil Rush need DLC 2 (head and meta 'dlc')."""
import uuid
import common as C
NAME='[FA] [2v2] Coal Mountain 0.1'
SKIRMISH_NAME='[FA] [2v2] Coal Mountain Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=3,Delta=4,Echo=4,Foxtrot=4,Golf=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Coal Mountain' and meta['gameVersion'] in C.SOURCE_VERSIONS and head['dlc']==meta['dlc']==[3]
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18],'authored map has a script or cameras now. Check this merge.'
    C.remove_units_and_waypoints(objects,units=8,waypoints=3)
    C.strip_editor_teams(objects,meta)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7)
    assert C.face_spawn_outliers(objects)=={'Spawn point 9':50}
    C.add_team_cameras(objects)
    if C.GRAFT_UIDS&{o['_uid'] for o in objects}:C.free_uids(objects,nodes)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
