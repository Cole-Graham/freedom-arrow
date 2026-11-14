"""[FA] [5v5] Oil Rush: Lateralus's Oil refinery layout (12 November 2026), with FA conquest and a camera for each team.
His spawn facings are kept. The export had seven HMMWVs owned by Alpha Player 1 parked on Bravo's spawn points (an editor
test); the build removes all placed units, so neither side starts with units.
0.2 (Lateralus 14 Nov 2026): zone values only. Echo 3 -> 4, Foxtrot 3 -> 4, Hotel 2 -> 3."""
import uuid
import common as C
NAME='[FA] [5v5] Oil Rush 0.2'
SKIRMISH_NAME='[FA] [5v5] Oil Rush Skirmish 0.2'
# Lateralus 2026-11-12; 0.2 values 2026-11-14.
VALUES=dict(Alpha=2,Bravo=3,Charlie=3,Delta=2,Echo=4,Foxtrot=4,Golf=2,Hotel=3,India=2,Juliett=3,Kilo=3)
LETTERS={n:(n,v) for n,v in VALUES.items()}
UNIT=1
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Oil refinery' and meta['gameVersion']==C.GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18],'authored map has a script or cameras now. Check this merge.'
    units=[o for o in objects if o.get('_type')==UNIT]
    assert {o['_dname'][:5] for o in units}<={'HMMWV'} and len(units)==7,'placed units changed. Check this merge.'
    objects[:]=[o for o in objects if o.get('_type')!=UNIT]
    C.strip_editor_teams(objects,meta)
    # Spawn points 6, 7 and 9 use UIDs 69, 70 and 72, which the FA lobby options need.
    assert C.free_uids(objects,nodes)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7)
    C.add_team_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
