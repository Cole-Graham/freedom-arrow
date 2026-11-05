"""[FA] [2v2] Dead Center: layout.bascr in this package, overlaid onto native network and Skirmish hosts."""
import common as C
NAME='[FA] [2v2] Dead Center 0.1';GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003'
SKIRMISH_NAME='[FA] [2v2] Dead Center Skirmish 0.1';SKIRMISH_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c004'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
      'the side with the higher zone value scores the difference. First to 300 wins. A B G H I J are worth 4, C D are worth 3, E F are worth 2. Flat 200 income, no upkeep.')
ZONE_VALUES=dict(Alpha=4,Bravo=4,Charlie=3,Delta=3,Echo=2,Foxtrot=2,Golf=4,Hotel=4,India=4,Juliet=4)
MAP_LENGTH=9000;FLANK_MARGIN=1200
def set_playable(objects):
    zones=[o for o in objects if o.get('_type')==15];play=[o for o in objects if o.get('_type')==7]
    assert zones and play and all(C.identity(o['rotate']) for o in play)
    west=min(o['pos']['X']-C.world_x_half(o) for o in zones);east=max(o['pos']['X']+C.world_x_half(o) for o in zones)
    width=east-west+2*FLANK_MARGIN;cx=(west+east)/2
    assert 0<=west-FLANK_MARGIN and east+FLANK_MARGIN<=MAP_LENGTH,(west,east)
    for o in play:
        o['pos']['X']=cx;o['pos']['Z']=MAP_LENGTH/2;o['scale']['X']=width;o['scale']['Z']=MAP_LENGTH;C.mag(o['pos']);C.mag(o['scale'])
    return west,east,width
def patch_host(head,nodes,objects,meta,flavor):
    kind=flavor['kind']
    assert head['GameMode']==kind and head['map']=='Central Village'
    want={str(o['_uid']):ZONE_VALUES[o['hudText']] for o in objects if o.get('_type')==15}
    assert len(want)==len(ZONE_VALUES) and want==C.weights(flavor['name']),want
    hits=shown=caps=0
    zones={f"c{o['_uid']}" for o in objects if o.get('_type')==15}
    for n in nodes['b']:
        if n.get('nnKey')=='setConquestMode':hits+=1
        if n.get('nnKey')=='objVisible2':
            props={p['k']:p for p in n['props_v2']}
            if props['oz2']['v'] in zones and props['isv']['v']=='False':props['isv']['v']='True';shown+=1
        if n.get('nnKey')=='setIncomeCurveState':
            for p in n['props_v2']:
                if p['k']=='state':p['v']='False'
        if n.get('nnKey')=='setMaxMoney':
            next(p for p in n['props_v2'] if p['k']=='moneyValue')['v']=str(C.MONEY_CAP);caps+=1
    assert hits>=1,'scenario must use ConquestMode'
    assert caps==(1 if kind==2 else 0),caps
    assert shown==(4 if kind==2 else 5),shown
    calcs={c['b'] for c in nodes['c'] if c['d']=='Multiply' and c['c']=='amount' and any(b['id']==c['a'] and b.get('nnKey')=='setMoney2' for b in nodes['b'])}
    assert len(calcs)==(2 if kind==3 else 0),calcs
    byid={b['id']:b for b in nodes['b']}
    for calc in calcs:
        source=[c['b'] for c in nodes['c'] if c['a']==calc and c['c']=='a'];assert len(source)==1
        assert not [c for c in nodes['c'] if c['a']==source[0] and c['c']=='Value'],'money variable has an input'
        nodes['c']=[c for c in nodes['c'] if not (c['a']==calc and c['c']=='B')]
        next(p for p in byid[calc]['props_v2'] if p['k']=='B')['v']='1'
        next(p for p in byid[source[0]]['props_v2'] if p['k']=='Value')['v']=str(C.START_POINTS)
    C.slider_defaults(objects,meta,2 if kind==2 else 0)
def prepare(game,spec):
    objects=C.read_layout(__file__)[2]
    west,east,width=set_playable(objects)
    print(f"layout playable width {width:.3f} m (zones {west:.3f}..{east:.3f}, flanks {FLANK_MARGIN})")
    return C.extract_layout(objects),None
SPEC=dict(
    author='Freedom Arrow',desc=DESC,prepare=prepare,patch_host=patch_host,
    flavors=[
        dict(name=NAME,guid=GUID,kind=2,public=True,host=C.NETWORK_HOST,deploy_target=159,deploy_pin='in'),
        dict(name=SKIRMISH_NAME,guid=SKIRMISH_GUID,kind=3,public=False,host=C.SKIRMISH_HOST),
    ],
)
def build(game,out):C.build_pair(game,out,SPEC)
