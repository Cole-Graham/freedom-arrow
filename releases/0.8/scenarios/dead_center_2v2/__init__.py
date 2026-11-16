"""[FA] [2v2] Dead Center: layout.bascr in this package, overlaid onto native network and Skirmish hosts."""
import common as C
import uuid
# 0.2 (Lateralus 16 Nov 2026): his zone, spawn and camera edits. 0.1 used fixed GUIDs ...c003/c004 (retired in Runtime.cs).
NAME='[FA] [2v2] Dead Center 0.2';GUID=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME))
SKIRMISH_NAME='[FA] [2v2] Dead Center Skirmish 0.2';SKIRMISH_GUID=str(uuid.uuid5(uuid.NAMESPACE_URL,SKIRMISH_NAME))
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
      'the side with the higher zone value scores the difference. First to 300 wins. A B G H I J are worth 4, C D are worth 3, E F are worth 2. Flat 200 income, no upkeep.')
ZONE_VALUES=dict(Alpha=4,Bravo=4,Charlie=3,Delta=3,Echo=2,Foxtrot=2,Golf=4,Hotel=4,India=4,Juliet=4)
# 0.2: the playable zone is Lateralus's own (his edited file, X 1677..6997); the build no longer computes it from the zones
# (0.1 did: zone span + 1200 each side, + 250 east). The map build checks that every ground spawn is inside it.
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
    return C.extract_layout(objects),None
SPEC=dict(
    author='Freedom Arrow',desc=DESC,prepare=prepare,patch_host=patch_host,
    flavors=[
        dict(name=NAME,guid=GUID,kind=2,public=True,host=C.NETWORK_HOST,deploy_target=159,deploy_pin='in'),
        dict(name=SKIRMISH_NAME,guid=SKIRMISH_GUID,kind=3,public=False,host=C.SKIRMISH_HOST),
    ],
)
def build(game,out):C.build_pair(game,out,SPEC)
