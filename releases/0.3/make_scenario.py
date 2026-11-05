"""Build [FA] Central Village from the game's own Central Village_network mission."""
from pathlib import Path
import argparse, hashlib, json, re, sys, zipfile
from Crypto.Cipher import AES
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3';NAME='[FA] Central Village';START_POINTS=1500;GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 3 minute opening, '
      'the side with the higher zone value scores the difference. A B G H I J are worth 4, C D are worth 3, E F are worth 2. Flat 200 income, no upkeep.')
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
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    src=a.game_dir/'BrokenArrow_Data/StreamingAssets/SharedMissions/Central Village_network'
    z=zipfile.ZipFile(src/'Central Village_network.bascr');head=load(dec(z.read('head.bam')));nodes=load(dec(z.read('nodes.bam')));objects=load(dec(z.read('objects.bam')))
    assert head['GameMode']==2 and head['map']=='Central Village'
    # Scoring reads zone values by ID. Fail the build if the letters and IDs ever disagree.
    want={str(o['_uid']):ZONE_VALUES[o['hudText']] for o in objects if o.get('_type')==15}
    assert len(want)==len(ZONE_VALUES) and want==json.loads((R/'source/UserData/FAConquestPrototype/settings.json').read_text())['MapZoneWeights'][NAME],want
    head.update(guid=GUID,name=NAME,author='Freedom Arrow',desc=DESC,IsDevVersion=False,devId=0,public=True)
    hits=0
    for n in nodes['b']:
        if n.get('nnKey')=='setConquestMode':hits+=1
        if n.get('nnKey')=='setIncomeCurveState':
            for p in n['props_v2']:
                if p['k']=='state':p['v']='False'
    assert hits>=1,'scenario must use ConquestMode'
    meta=load((src/'meta.json').read_bytes());meta.pop('devid',None)
    # The lobby slider runs 500 to 1500. Default it to the top.
    money=[o for o in objects if o.get('desc')=='ui_lobby_StartMoney_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_StartMoney_desc']
    assert len(money)==2
    for o in money:
        o['defV']=START_POINTS
        if 'tstV' in o:o['tstV']=START_POINTS
    meta.update(guid=GUID,scenario=NAME,author='Freedom Arrow',desc=DESC,public=True)
    meta.update(type=2)
    out=a.out/NAME;out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out/(NAME+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for name,data in [('head.bam',dump(head)),('objects.bam',dump(objects)),('nodes.bam',dump(nodes))]:
            w.writestr(zipfile.ZipInfo(name,(2026,11,4,0,0,0)),enc(data),zipfile.ZIP_DEFLATED)
    (out/'meta.json').write_bytes(dump(meta))
    print(out)
if __name__=='__main__':main()
