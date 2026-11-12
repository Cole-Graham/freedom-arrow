"""[FA] [2v2] Chkalovsk Airbase: Lateralus's authored layout on the Airbase scene, FA script grafted. Authored objectives preserved; playable bounds activated and cropped beyond Alpha."""
import math
import common as C
NAME='[FA] [2v2] Chkalovsk Airbase 0.1';GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c007'
SKIRMISH_NAME='[FA] [2v2] Chkalovsk Airbase Skirmish 0.1';SKIRMISH_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c008'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
      'the side with the higher zone value scores the difference. First to 300 wins. A B C are worth 2, D E are worth 3, F G are worth 4. Flat 200 income, no upkeep.')
# Authored zone name -> (shown name, value). Lateralus 2026-11-07: the authored Hotel is Foxtrot.
LETTERS=dict(Alpha=('Alpha',2),Bravo=('Bravo',2),Charlie=('Charlie',2),Delta=('Delta',3),Echo=('Echo',3),Hotel=('Foxtrot',4),Golf=('Golf',4))
CONQUEST_NODE=136
# Alpha spawns west and Bravo east. Each camera stands on its own side of the zone centre, on the west-east axis,
# and looks toward the centre. Distances are from vanilla Airbase_network: camera 2300 m and look-at 1100 m from the centre.
CAMERA_BACK=2300.0;LOOK_BACK=1100.0;GROUND_Y=136.0;HEIGHT=700.0
def add_start_cameras(objects):
    zones=[o['pos'] for o in objects if o.get('_type')==15]
    cx=sum(p['X'] for p in zones)/len(zones);cz=sum(p['Z'] for p in zones)/len(zones)
    spawns={o['team']['id']:o['pos']['X'] for o in objects if o.get('_type')==10}
    teams={o['_dname']:o['_uid'] for o in objects if o.get('_type')==3}
    for team,name,side in (('Alpha team','Camera alpha',-1),('Bravo team','Camera bravo',1)):
        assert all((x-cx)*side>0 for t,x in spawns.items() if t==teams[team]),(team,'spawns on the other side')
        C.add_camera(objects,team,name,dict(X=cx+side*CAMERA_BACK,Y=GROUND_Y,Z=cz),dict(X=cx+side*LOOK_BACK,Y=GROUND_Y,Z=cz),HEIGHT)
# Lateralus 2026-11-07: Bravo's north-east spawn (Spawn point 5) was exported facing north. Turn it toward the zone centre,
# like the other spawns. The build stops if a new export already sets its facing.
def face_spawn(objects,name):
    zones=[o['pos'] for o in objects if o.get('_type')==15]
    cx=sum(p['X'] for p in zones)/len(zones);cz=sum(p['Z'] for p in zones)/len(zones)
    o=next(o for o in objects if o.get('_type')==10 and o['_dname']==name)
    assert C.identity(o['rotate']),(name,'already has a facing. Remove face_spawn.')
    half=math.atan2(cx-o['pos']['X'],cz-o['pos']['Z'])/2
    o['rotate'].update(X=0.0,Y=math.sin(half),Z=0.0,W=math.cos(half))
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Airbase' and meta['gameVersion']==C.GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and 'pblOpt' not in meta,'authored map has a script now. Check this merge.'
    assert not [o for o in objects if o.get('_type')==18],'authored map has cameras now. Check this merge.'
    # The authored object existed but spz=0 left it inactive. Three sides meet the map limits;
    # the fourth is 1500 engine units beyond Alpha's centre, away from Charlie.
    alpha=next(o for o in objects if o.get('_type')==15 and o['_dname']=='Alpha')
    charlie=next(o for o in objects if o.get('_type')==15 and o['_dname']=='Charlie')
    assert alpha['pos']['Z']>charlie['pos']['Z']
    edge=alpha['pos']['Z']+1500.0;assert 4040.42578<edge<=9000.0
    play=next(o for o in objects if o.get('_type')==7)
    play['pos']=C.vec(dict(X=4500,Y=136,Z=edge/2));play['scale']=C.vec(dict(X=9000,Y=1,Z=edge))
    play['rotate']=dict(X=0.0,Y=0.0,Z=0.0,W=1.0);head['spz']=play['_uid']
    C.strip_editor_teams(objects,meta)
    C.letter_zones(objects,LETTERS,[fl['name'] for fl in spec['flavors']])
    face_spawn(objects,'Spawn point 5')
    add_start_cameras(objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(
    author='Lateralus',desc=DESC,prepare=prepare,
    flavors=[
        dict(name=NAME,guid=GUID,kind=2,public=True,deploy_target=CONQUEST_NODE,deploy_pin='in2'),
        dict(name=SKIRMISH_NAME,guid=SKIRMISH_GUID,kind=3,public=False),
    ],
)
def build(game,out):C.build_pair(game,out,SPEC)
