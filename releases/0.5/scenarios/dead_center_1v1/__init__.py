"""[FA] [1v1] Dead Center: authored layout in this package, FA script grafted. Zones, spawns and playable stay put."""
import common as C
NAME='[FA] [1v1] Dead Center 0.1';GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c005'
SKIRMISH_NAME='[FA] [1v1] Dead Center Skirmish 0.1';SKIRMISH_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c006'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
      'the side with the higher zone value scores the difference. First to 300 wins. A B C are worth 2, D E are worth 3. Flat 200 income, no upkeep.')
LETTERS=dict(A=('Alpha',2),B=('Bravo',2),C=('Charlie',2),D=('Delta',3),E=('Echo',3))
CONQUEST_NODE=136
def add_start_cameras(game,objects):
    # Same starting cameras and look-at points as vanilla Central Village.
    native=C.read_native(game,C.NETWORK_HOST)[2];tags={o['_uid']:o for o in native if o.get('_type')==6}
    cams={o['_dname']:o for o in native if o.get('_type')==18}
    assert set(cams)=={'Camera alpha','Camera bravo'}
    for team,name in (('Alpha team','Camera alpha'),('Bravo team','Camera bravo')):
        cam=cams[name];C.add_camera(objects,team,name,cam['pos'],tags[cam['aimTag']['id']]['pos'],cam['height'])
def prepare_letter_zones(objects,names):
    zones=[o for o in objects if o.get('_type')==15]
    want={str(o['_uid']):LETTERS[o['_dname']][1] for o in zones}
    assert {o['_dname'] for o in zones}==set(LETTERS)
    for name in names:assert want==C.weights(name),(name,want)
    teams={o['_dname']:o['_uid'] for o in objects if o.get('_type')==3}
    for o in zones:
        o['hudText']=LETTERS[o['_dname']][0]
        o['capturableBy']=[c for c in o['capturableBy'] if c['id'] in (teams['Alpha team'],teams['Bravo team'])];assert len(o['capturableBy'])==2
def prepare(game,spec):
    head,nodes,objects,meta=C.read_layout(__file__)
    assert head['map']=='Central Village' and meta['gameVersion']==C.GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and 'pblOpt' not in meta,'authored map has a script now. Check this merge.'
    C.strip_editor_teams(objects,meta)
    prepare_letter_zones(objects,[fl['name'] for fl in spec['flavors']])
    add_start_cameras(game,objects)
    return C.extract_layout(objects),(head,nodes,objects,meta)
SPEC=dict(
    author='Lateralus',desc=DESC,prepare=prepare,
    flavors=[
        dict(name=NAME,guid=GUID,kind=2,public=True,deploy_target=CONQUEST_NODE,deploy_pin='in2'),
        dict(name=SKIRMISH_NAME,guid=SKIRMISH_GUID,kind=3,public=False),
    ],
)
def build(game,out):C.build_pair(game,out,SPEC)
