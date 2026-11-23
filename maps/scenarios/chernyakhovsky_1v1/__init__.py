"""[FA] [1v1] Chernyakhovsky: Lateralus's new design (16 Nov 2026, thread 1571554273639006392: "Add this brand new design for Cherny to the
mod ... A B - 2 points, E D - 3 points, C F - 4 points. Don't change the version number, just replace the current version entirely").
It replaces End's CHERNYAKHOVSKY layout under the same name and GUID, so installed copies are updated in place. The layout has no script
and no cameras: the FA conquest graft supplies the script, as for Highway of Death. Zone IDs 31-36 match no other FA map."""
import uuid
import common as C
NAME='[FA] [1v1] Chernyakhovsky 0.1'
SKIRMISH_NAME='[FA] [1v1] Chernyakhovsky Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=4,Delta=3,Echo=3,Foxtrot=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Chernyakhovsk' and head['author']=='Lateralus' and meta['gameVersion'] in C.SOURCE_VERSIONS,(head['map'],meta['gameVersion'])
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type') in (1,18)]
    C.strip_editor_teams(objects,meta)
    assert C.free_uids(objects,nodes)=={}
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    C.letter_zones(objects,LETTERS,[f['name'] for f in spec['flavors']])
    for o in objects:
        if o.get('_type')==3 and o['_dname'] in ('Alpha team','Bravo team'):assert len(o['players'])==5,(o['_dname'],len(o['players']))
    pz=[o['_uid'] for o in objects if o.get('_type')==7];assert len(pz)==1;head['spz']=pz[0]
    C.face_spawns_to_objectives(objects)
    C.add_team_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
