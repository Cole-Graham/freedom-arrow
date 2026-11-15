"""[FA] [1v1] Kadaga: End's KADAGA layout (Steam Workshop 3832299239, updated 3 Nov 2026), with FA conquest and a camera for
each team. Osama 15 Nov 2026 00:54 PST: "End said we can use his maps here and implement them into our mod"; 00:56 "just apply our
gamemode and add it to the mod"; 01:01 "these are 1v1". End's own script (stock conquest, 300 points, 45 minutes, a 39 s pause)
is replaced by the FA conquest graft. Zone values (no values in End's file): Bravo, the centre zone, 3; the others 2."""
import uuid
import common as C
NAME='[FA] [1v1] Kadaga 0.1'
SKIRMISH_NAME='[FA] [1v1] Kadaga Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=3,Charlie=2,Delta=2,Echo=2)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Kadaga Military Base' and head['author']=='End' and meta['gameVersion']==C.GAME_VERSION
    assert not [o for o in objects if o.get('_type') in (1,18)],'authored map has units or cameras now. Check this merge.'
    assert [b['nnKey'] for b in nodes['b']]==['start','delay','pauseGame','pauseGame','setConquestMode'],'End changed his script. Check this merge.'
    nodes.update(b=[],c=[])   # the FA conquest graft supplies the script
    C.strip_editor_teams(objects,meta)
    assert C.free_uids(objects,nodes)=={}
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    pz=[o['_uid'] for o in objects if o.get('_type')==7];assert len(pz)==1 and head['spz'] in (0,pz[0])
    head['spz']=pz[0]   # End's file leaves the active play area unset; the other FA maps name their one play area
    C.add_team_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='End',desc=C.describe(VALUES,100)+' Map by End.',prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
