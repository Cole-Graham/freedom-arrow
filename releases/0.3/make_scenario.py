"""Build [FA] Central Village from the game's own Central Village_network mission."""
from pathlib import Path
import argparse, hashlib, json, re, sys, zipfile
from Crypto.Cipher import AES
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3';NAME='[FA] Central Village';GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 3 minute opening, '
      'the side holding more zones scores the difference. Flat 200 income, no upkeep.')
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
    z=zipfile.ZipFile(src/'Central Village_network.bascr');head=load(dec(z.read('head.bam')));nodes=load(dec(z.read('nodes.bam')));objects=dec(z.read('objects.bam'))
    assert head['GameMode']==2 and head['map']=='Central Village'
    head.update(guid=GUID,name=NAME,author='Freedom Arrow',desc=DESC,IsDevVersion=False,devId=0,public=True)
    hits=0
    for n in nodes['b']:
        if n.get('nnKey')=='setConquestMode':hits+=1
        if n.get('nnKey')=='setIncomeCurveState':
            for p in n['props_v2']:
                if p['k']=='state':p['v']='False'
    assert hits>=1,'scenario must use ConquestMode'
    meta=load((src/'meta.json').read_bytes());meta.pop('devid',None)
    meta.update(guid=GUID,scenario=NAME,author='Freedom Arrow',desc=DESC,public=True)
    meta.update(type=2)
    out=a.out/NAME;out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out/(NAME+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for name,data in [('head.bam',dump(head)),('objects.bam',objects),('nodes.bam',dump(nodes))]:
            w.writestr(zipfile.ZipInfo(name,(2026,11,4,0,0,0)),enc(data),zipfile.ZIP_DEFLATED)
    (out/'meta.json').write_bytes(dump(meta))
    print(out)
if __name__=='__main__':main()
