"""[FA] [3v3] Bay of Winds: Lateralus's new map on Parnu (20 Nov 2026, thread 1572962048705429598: "add this map to the mod, using these zone
values. Don't forget to add the cameras, and make sure all the settings are the same as the other maps in the mod. Also, remove the humvees
and 4 waypoints. A B C D - 2 points, E F I J - 3 points, G H K L - 4 points"). The layout has no script and no cameras: the FA conquest graft
supplies the script and add_team_cameras the cameras, as for Chernyakhovsky. The 8 Humvees (type 1) and 4 waypoints (type 19) are removed.
Zone IDs 30-41 match no other FA map."""
import uuid
import common as C
NAME='[FA] [3v3] Bay of Winds 0.1'
SKIRMISH_NAME='[FA] [3v3] Bay of Winds Skirmish 0.1'
VALUES=dict(Alpha=2,Bravo=2,Charlie=2,Delta=2,Echo=3,Foxtrot=3,India=3,Juliett=3,Golf=4,Hotel=4,Kilo=4,Lima=4)
LETTERS={n:(n,v) for n,v in VALUES.items()}
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Parnu' and head['author']=='Lateralus' and meta['gameVersion'] in C.SOURCE_VERSIONS,(head['map'],meta['gameVersion'])
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type')==18]
    drop={o['_uid'] for o in objects if o.get('_type') in (1,19)}
    assert len(drop)==12 and sum(1 for o in objects if o.get('_type')==1)==8,len(drop)
    objects[:]=[o for o in objects if o['_uid'] not in drop]
    assert drop.isdisjoint(C_links(objects)),'an object links to a removed Humvee or waypoint'
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
def C_links(objects):
    """Every {'id','type'} link id in the objects."""
    ids=set()
    def walk(v):
        if isinstance(v,dict):
            if set(v)=={'id','type'}:ids.add(v['id'])
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(objects);return ids
SPEC=dict(author='Lateralus',desc=C.describe(VALUES),prepare=prepare,flavors=[
    dict(name=NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
    dict(name=SKIRMISH_NAME,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME)),kind=3,public=False)])
def build(game,out):C.build_pair(game,out,SPEC)
