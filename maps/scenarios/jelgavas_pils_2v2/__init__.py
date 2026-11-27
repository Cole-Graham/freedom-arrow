"""[FA] [2v2] Jelgavas Pils: Lateralus's Jelgavas Pils layout on the Jelgava terrain (27 November 2026, FA_2v2_Jelgavas_Pils_0.1.zip in thread
1572962048705429598), with FA conquest and a camera per team.
Lateralus 27 Nov 2026: "add this map to the mod / A B - 2 points / C D - 4 points".
- His nine test units (Konkurs, BTR-82A, Stryker ESV and ICV) and three waypoints are removed; the editor's Neutral and Spectators teams too.
- 2 ground, 1 helicopter and 1 air spawn per team. The start camera sits between each team's two ground spawns (C.add_team_cameras(ground=True)).
- Bravo's Spawn point 5 (ground) faced 51 degrees away from the zones; it now faces them. His other facings are kept.
- No DLC listed. Not checked in game."""
import uuid
import common as C
NAME='[FA] [2v2] Jelgavas Pils 0.1'
SKIRMISH_NAME='[FA] [2v2] Jelgavas Pils Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=4,Delta=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Jelgava' and meta['gameVersion'] in C.SOURCE_VERSIONS and not head['dlc'] and not meta['dlc']
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18],'authored map has a script or cameras now. Check this merge.'
    C.remove_units_and_waypoints(objects,units=9,waypoints=3)
    C.strip_editor_teams(objects,meta)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7)
    assert C.face_spawn_outliers(objects)=={'Spawn point 5':51}
    C.add_team_cameras(objects,ground=True)
    if C.GRAFT_UIDS&{o['_uid'] for o in objects}:C.free_uids(objects,nodes)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
