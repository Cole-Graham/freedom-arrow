"""[FA] [1v1] Kadaga Military Base: Lateralus's new 1v1 design on the Kadaga Military Base terrain (28 November 2026,
FA_1v1_Kadaga_Military_Base_0.1.zip in thread 1568104480459722894), with FA conquest and a camera per team. It replaces [FA] [1v1] Kadaga.
Lateralus 28 Nov 2026: "Remove Kadaga 1v1, and add this completely new design, it should be in ranked / A B - 3 points / C D - 4 points".
- His six test units (Stryker ESV and ICVs, BTR-82A, BTR-90s) and three waypoints are removed; the editor's Neutral and Spectators teams too.
- Alpha has 2 ground spawns, Bravo 3 (as authored); 1 helicopter and 1 air spawn each. The start camera sits over each team's ground spawns
  (C.add_team_cameras(ground=True)).
- Every spawn already faces the zones within 45 degrees; his facings are kept.
- DLC 2, as the old Kadaga. Not checked in game."""
import uuid
import common as C
NAME='[FA] [1v1] Kadaga Military Base 0.1'
SKIRMISH_NAME='[FA] [1v1] Kadaga Military Base Skirmish 0.1'
VALUES=dict(Alpha=3,Bravo=3,Charlie=4,Delta=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Kadaga Military Base' and meta['gameVersion'] in C.SOURCE_VERSIONS and head['dlc']==meta['dlc']==[2]
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18],'authored map has a script or cameras now. Check this merge.'
    C.remove_units_and_waypoints(objects,units=6,waypoints=3)
    C.strip_editor_teams(objects,meta)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7)
    assert C.face_spawn_outliers(objects)=={},'every spawn faced the zones (within 45 degrees) when added'
    C.add_team_cameras(objects,ground=True)
    if C.GRAFT_UIDS&{o['_uid'] for o in objects}:C.free_uids(objects,nodes)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
