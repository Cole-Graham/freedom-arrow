"""Build [FA] Central Village from the game's own Central Village_network mission."""
from pathlib import Path
import argparse, hashlib, json, re, sys, zipfile
from Crypto.Cipher import AES
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3';NAME='[FA] Central Village';START_POINTS=1500;GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 3 minute opening, '
      'the side with the higher zone value scores the difference. A B G H I J are worth 4, C D are worth 3, E F are worth 2. Flat 200 income, no upkeep.')
SKIRMISH_NAME='[FA] Central Village Skirmish';SKIRMISH_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c004'
ZONE_VALUES=dict(Alpha=4,Bravo=4,Charlie=3,Delta=3,Echo=2,Foxtrot=2,Golf=4,Hotel=4,India=4,Juliet=4)
def dec(raw):
    assert raw[:8]==MARKER
    p=AES.new(AES_KEY,AES.MODE_CBC,raw[8:24]).decrypt(raw[24:]);return p[:-p[-1]]
def enc(p):
    # IV comes from the content, so the same input gives the same file on every build machine.
    iv=hashlib.sha256(p).digest()[:16];n=16-len(p)%16
    return MARKER+iv+AES.new(AES_KEY,AES.MODE_CBC,iv).encrypt(p+bytes([n])*n)
def load(b):return json.loads(b.decode('utf-8-sig'))
def dump(o):return json.dumps(o,indent=2,ensure_ascii=False).encode('utf-8')
def build(game,out,name,guid,mission,kind,desc,public):
    src=game/'BrokenArrow_Data/StreamingAssets/SharedMissions'/mission
    z=zipfile.ZipFile(src/(mission+'.bascr'));head=load(dec(z.read('head.bam')));nodes=load(dec(z.read('nodes.bam')));objects=load(dec(z.read('objects.bam')))
    assert head['GameMode']==kind and head['map']=='Central Village'
    # Scoring reads zone values by ID. Fail the build if the letters and IDs ever disagree.
    want={str(o['_uid']):ZONE_VALUES[o['hudText']] for o in objects if o.get('_type')==15}
    assert len(want)==len(ZONE_VALUES) and want==json.loads((R/'source/UserData/FAConquestPrototype/settings.json').read_text())['MapZoneWeights'][name],want
    head.update(guid=guid,name=name,author='Freedom Arrow',desc=desc,IsDevVersion=False,devId=0,public=public)
    hits=shown=0
    zones={f"c{o['_uid']}" for o in objects if o.get('_type')==15}
    for n in nodes['b']:
        if n.get('nnKey')=='setConquestMode':hits+=1
        # The small map size hides outer zones, and Auto picks small under 8 players. Every zone stays in FA.
        if n.get('nnKey')=='objVisible2':
            props={p['k']:p for p in n['props_v2']}
            if props['oz2']['v'] in zones and props['isv']['v']=='False':props['isv']['v']='True';shown+=1
        if n.get('nnKey')=='setIncomeCurveState':
            for p in n['props_v2']:
                if p['k']=='state':p['v']='False'
    assert hits>=1,'scenario must use ConquestMode'
    assert shown==(4 if kind==2 else 5),shown
    meta=load((src/'meta.json').read_bytes());meta.pop('devid',None)
    # The lobby slider runs 500 to 1500. Default it to the top. Skirmish missions have no slider.
    money=[o for o in objects if o.get('desc')=='ui_lobby_StartMoney_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_StartMoney_desc']
    assert len(money)==(2 if kind==2 else 0)
    for o in money:
        o['defV']=START_POINTS
        if 'tstV' in o:o['tstV']=START_POINTS
    meta.update(guid=guid,scenario=name,author='Freedom Arrow',desc=desc,public=public,type=kind)
    target=out/name;target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target/(name+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for part,data in [('head.bam',dump(head)),('objects.bam',dump(objects)),('nodes.bam',dump(nodes))]:
            w.writestr(zipfile.ZipInfo(part,(2026,11,4,0,0,0)),enc(data),zipfile.ZIP_DEFLATED)
    (target/'meta.json').write_bytes(dump(meta))
    print(target)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    build(a.game_dir,a.out,NAME,GUID,'Central Village_network',2,DESC,True)
    # F8 Local AI lists Skirmish scenarios only, because PVP missions have no bot slots.
    build(a.game_dir,a.out,SKIRMISH_NAME,SKIRMISH_GUID,'Central_Village_Skirmish',3,DESC,False)
if __name__=='__main__':main()
