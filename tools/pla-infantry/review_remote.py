"""Run on the test PC: select each native armory card and retain real screenshots.

Requires the opt-in PLA review helper and an already open, focused test armory.
It never starts a match or activates a desktop window.
"""
from pathlib import Path
import argparse,json,subprocess,time
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--window',required=True);a=ap.parse_args();r=a.root.resolve();d=r/'game/UserData/FAModels';out=r/'logs/review';out.mkdir(exist_ok=True);configs=json.loads((r/'game/UserData/FreedomArrow/pla-infantry-configurations.json').read_text());results=[]
assert len(configs)==25 and r.name.startswith('BA-Codex-PLA-Configs-')
for c in configs:
 uid=c['unit'];(d/'pla-review-unit.txt').write_text(str(uid)+':aligned-all25-'+str(time.time())+'\n');state={};deadline=time.monotonic()+40
 while time.monotonic()<deadline:
  try:state=json.loads((d/'pla-review-state.json').read_text())
  except (FileNotFoundError,json.JSONDecodeError):pass
  if state.get('displayed')==uid and state.get('requested')==uid and state.get('applied',0)>=21 and state.get('failed',1)==0:break
  time.sleep(.5)
 else:raise RuntimeError('Native card/body readiness failed: '+json.dumps(c)+' '+json.dumps(state))
 time.sleep(3)
 wins=json.loads(subprocess.check_output([str(Path.home()/'.vengeance/bin/v-window'),'list','--json']))['windows'];active=next(w for w in wins if w['active']);assert active['id']==a.window,'Desktop focus changed; screenshot stopped'
 shot=out/(str(uid)+'-'+c['key']+'.png');subprocess.run([str(Path.home()/'.vengeance/bin/v-shot'),'active','-o',str(shot)],check=True,stdout=subprocess.DEVNULL)
 log=(r/'game/MelonLoader/Latest.log').read_text(errors='replace');lines=[x for x in log.splitlines() if 'body applied unit='+str(uid)+' ' in x];assert len(lines)>=21,(uid,len(lines));assert all('file=pla2_'+c['key']+'_' in x for x in lines),(uid,'wrong mesh binding')
 result={**c,**state,'screenshot':str(shot),'successful_body_log_entries':len(lines)};results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print('REVIEW',len(results),uid,c['label'],'applied',state['applied'],'failed',state['failed'],flush=True)
print('All25 native armory cards and their bodies checked',flush=True)
