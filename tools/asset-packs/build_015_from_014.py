"""Build LIVE assets 0.1.15 from the exact pinned 0.1.14; only the music DLL changes."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,subprocess,tempfile,zipfile
from zoneinfo import ZoneInfo
BASE_SHA='1683bae9270a1d19e43cba662c93f92a5002635c1d61841191762701d25ac153'
VERSION='0.1.15'
MUSIC_SHA='ce190009d50b5e71f9dcb5e6a13ca738eb03e2664ab4b156ba4bc8a011bea7f5'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def enc(o):return (json.dumps(o,indent=2)+'\n').encode()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base',required=True,type=Path);ap.add_argument('--music-dll',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--zip',default='zip');a=ap.parse_args()
 assert sha(a.base)==BASE_SHA,'Base is not the pinned LIVE assets 0.1.14'
 dll=a.music_dll.read_bytes();assert hashlib.sha256(dll).hexdigest()==MUSIC_SHA,'Music DLL is not the verified 1.5.1 candidate'
 output=a.output.resolve();assert output!=a.base.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 stamp=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z (America/Los_Angeles)')
 with zipfile.ZipFile(a.base) as old:
  names=old.namelist();assert len(names)==len(set(names));m=json.loads(old.read('UserData/FAAssets/manifest.json'));mod=json.loads(old.read('mod.json'))
  assert m['id']==mod['id']=='freedomarrow.assets.live' and m['version']==mod['version']=='0.1.14';assert mod['type']=='mod'
  assert not any(n.startswith('UserData/FreedomArrow/') for n in names)
  assert not any(n in names for n in ('UserData/FAMusic/pack.txt','UserData/FAMusic/music-history.txt'))
  change={'Mods/FAMusic.dll':dll};m['version']=VERSION;m['files']['Mods/FAMusic.dll']=hashlib.sha256(dll).hexdigest()
  m['notes'].append('FA Music 1.5.1: native Home music selector with flags/emblem and loaded LIVE version above it. Existing models, music and voice files retained. UI previously tested with 1.5.0 on PLA; LIVE version fallback checked in source/host tests, new LIVE run pending.')
  change['UserData/FAAssets/manifest.json']=enc(m);mod['version']=VERSION;change['mod.json']=enc(mod)
  readme=old.read('README.md').decode();heading='## Document change log';assert readme.count(heading)==1
  body,ledger=readme.split(heading)
  lead='**LIVE Models and Music 0.1.15 includes FA Music 1.5.1: the bottom-centre Home selector with flag/emblem, pack name and click-to-cycle. The loaded Freedom Arrow version appears above it.**\n\nAll 0.1.14 models, songs and voices are unchanged. Existing music selection is retained. This is the separate LIVE cosmetic/music asset package, compatible with the pinned gameplay dev.45 and main development dev.55; compatibility is read from the source/API, not established by a fresh LIVE game run. No PLA units or gameplay constants are included. Public deployment pins are unchanged.\n\n## Earlier package history\n\n'
  change['README.md']=(lead+body+heading+ledger.rstrip()+'\n- '+stamp+' — Added FA Music 1.5.1 native Home selector and LIVE version identity; all existing model/audio/voice payload bytes retained.\n').encode()
  subprocess.run(['cp','--reflink=auto',str(a.base.resolve()),str(output)],check=True)
  with tempfile.TemporaryDirectory(prefix='fa-live-music-') as folder:
   tmp=Path(folder)
   for n,b in change.items():p=tmp/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   subprocess.run([a.zip,'-q',str(output),*change],cwd=tmp,check=True)
  with zipfile.ZipFile(output) as new:
   assert new.namelist() and len(new.namelist())==len(set(new.namelist()))
   assert set(new.namelist())==set(names)
   assert new.testzip() is None
   for n,h in m['files'].items():assert hashlib.sha256(new.read(n)).hexdigest()==h,n
   unchanged=[n for n in names if n not in change]
   for n in unchanged:assert new.read(n)==old.read(n),n
   assert json.loads(new.read('UserData/FAAssets/manifest.json'))['models']==json.loads(old.read('UserData/FAAssets/manifest.json'))['models']
   assert new.read('README.md').decode().count(heading)==1
  result={'stream':'live assets','version':VERSION,'file':output.name,'sha256':sha(output),'bytes':output.stat().st_size,'base_sha256':BASE_SHA,'music_version':'1.5.1','music_sha256':hashlib.sha256(dll).hexdigest(),'changed_paths':list(change),'verified_payloads':len(m['files']),'unchanged_archive_entries':len(unchanged),'native_live_tested':False,'published':False}
  output.with_suffix('.json').write_bytes(enc(result));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
