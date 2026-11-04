"""Verify this actual .bamod archive, without game data or a game launch."""
from pathlib import Path
import hashlib,json,sys,zipfile
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('FreedomArrow-0.1.1.bamod')
with zipfile.ZipFile(p) as z:
 names=z.namelist();assert len(set(names))==len(names)
 assert all(not n.startswith('/') and '..' not in Path(n).parts and '\\' not in n for n in names)
 expected={'Mods/BALocalSkirmish.dll','Mods/FreedomArrow.Runtime.dll','Mods/FreedomArrow.ConquestBatch.dll'}
 assert {n for n in names if n.startswith('Mods/')}==expected
 m=json.loads(z.read('UserData/FreedomArrow/payload-manifest.json'))
 for n,h in m['sha256'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 assert set(names)-{'mod.json','README.md','UserData/FreedomArrow/payload-manifest.json'}==set(m['sha256'])
 for name in ['units','weapons','sensors','sensor_units']:assert json.loads(z.read(f'UserData/FreedomArrow/constants/{name}.json'))=={}
 for row in json.loads(z.read('UserData/FreedomArrow/constants/options.json')).values():assert not {'StealthOverride','MainSensorId','ExtraSensorId'}&set(row)
 assert not any(k in n.lower() for n in names for k in ['ground-spotting','engine.json','probe.dll','armory-suite','behavior-tests'])
 s=json.loads(z.read('UserData/FAConquestPrototype/settings.json'))
 assert not s['ShowOverlay'] and not s['EnableDeveloperFixtures'] and s['TestDurationSeconds']==0 and s['ScoreLimit']==0 and s['Ending']=='time_limit'
 pins=json.loads(z.read('UserData/FAConquestPrototype/compatibility.json'))
 for f in ['Mods/BALocalSkirmish.dll','UserData/FAConquestPrototype/settings.json']:assert pins[f]==hashlib.sha256(z.read(f)).hexdigest()
 assert json.loads(z.read('mod.json'))['type']=='modpack'
 print(f'PASS: {len(m["sha256"])} payload hashes; vanilla spotting; no QA probes/debug panel settings; no temporary time/score fixture')
 print(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)
