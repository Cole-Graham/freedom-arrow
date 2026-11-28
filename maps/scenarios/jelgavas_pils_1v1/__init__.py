"""[FA] [1v1] Jelgavas Pils: Lateralus's 1v1 cut of his Jelgavas Pils layout (28 November 2026, FA_1v1_Jelgavas_Pils_0.1.zip in thread
1568104480459722894), with FA conquest and a camera per team. It replaces [FA] [1v1] Jelgava.
Lateralus 28 Nov 2026: "remove 1v1 Jelgava from the mod, and add this map instead and mark it as new (and still version 0.1). It should be
included in the ranked map pool. The zone values should be the same as the 2v2 version of this map".
- His file is the 2v2 layout (jelgavas_pils_2v2) with a narrower playable zone: 6000 -> 5000 m wide, centre 496 m east. Every zone, spawn,
  unit, waypoint and team is the same, so the build steps are the 2v2 steps: nine test units and three waypoints removed, the editor's Neutral
  and Spectators teams removed, Bravo's Spawn point 5 turned to face the zones (51 degrees off), the start camera between each team's two
  ground spawns.
- Zones A B 2 / C D 4 (31 32 33 34), the 2v2 values, so the two maps can share zone IDs (make_scenario.py checks that).
- No DLC listed. Not checked in game."""
import uuid
import common as C
NAME='[FA] [1v1] Jelgavas Pils 0.1'
SKIRMISH_NAME='[FA] [1v1] Jelgavas Pils Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=4,Delta=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Jelgava' and meta['gameVersion'] in C.SOURCE_VERSIONS and not head['dlc'] and not meta['dlc']
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18],'authored map has a script or cameras now. Check this merge.'
    zone=next(o for o in objects if o.get('_type')==7)
    assert (zone['scale']['X'],zone['scale']['Z'])==(5000.0,9000.0),zone['scale']
    C.remove_units_and_waypoints(objects,units=9,waypoints=3)
    C.strip_editor_teams(objects,meta)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==zone['_uid']
    assert C.face_spawn_outliers(objects)=={'Spawn point 5':51}
    C.add_team_cameras(objects,ground=True)
    if C.GRAFT_UIDS&{o['_uid'] for o in objects}:C.free_uids(objects,nodes)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
