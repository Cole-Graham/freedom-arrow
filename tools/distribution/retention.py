"""BA hosted artifact retention. Dry run by default; Drive removals use Trash, GitHub uses ba-gh."""
from pathlib import Path
import argparse,datetime,json,os,re,subprocess,sys,urllib.parse
ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex');sys.path.insert(0,str(ROOT/'bin'))
from virgil_google import api
BA_GH=ROOT/'bin/ba-gh';REPO='Cole-Graham/freedom-arrow'
FOLDERS={'1bphWHVjwoVTGzXSfwJj7f5jAT6UdzfTw','1vyjPPhmsm2Ul5BqUSA5_Vd99FjRAyoq9'}
REQUEST='https://discord.com/channels/1566969627743879208/1568104480459722894/1569914636072132609'
def classify(name):
 if m:=re.fullmatch(r'FreedomArrow-(\d+)\.(\d+)\.(\d+)-dev\.(\d+)\.bamod',name):return 'gameplay',tuple(map(int,m.groups()))
 if m:=re.fullmatch(r'FreedomArrow-Assets-(\d+)\.(\d+)\.(\d+)\.bamod',name):return 'assets',tuple(map(int,m.groups()))
 if m:=re.fullmatch(r'PLA-TEST-Build-(\d+)\.bamod',name):return 'pla',(1,int(m[1]))
 if m:=re.fullmatch(r'FreedomArrow-\d+\.\d+\.\d+-pla\.(.*)\.bamod',name):return 'pla',(0,0)
 if m:=re.fullmatch(r'FreedomArrow-\d+\.\d+\.\d+-devtest\.lat\.(\d+)\.bamod',name):return 'lateralus-test',(int(m[1]),)
 if name.startswith('FreedomArrow-Launcher') and name.endswith('.zip'):
  m=re.search(r'-v(\d+)\.zip$',name);return 'launcher',(int(m[1]) if m else 0,)
 return None

def plan_drive(items,protected_ids,protected_names):
 groups={};unknown=[]
 for x in items:
  if not FOLDERS.intersection(x.get('parents',[])):continue
  cls=classify(x['name'])
  if cls:groups.setdefault(cls[0],[]).append((cls[1],x))
  elif x['name'].endswith(('.bamod','.zip')) and x['name'].startswith(('FreedomArrow','PLA-')):unknown.append(x)
 keep=[];remove=[]
 for family,rows in groups.items():
  versions=sorted(set(v for v,x in rows),reverse=True)[:2]
  # Keep all locked/dependency links, and one exact copy per latest version unless a duplicate is linked.
  seen=set()
  for v,x in sorted(rows,key=lambda r:(r[0],r[1].get('createdTime','')),reverse=True):
   protected=x['id'] in protected_ids or x['name'] in protected_names
   target=keep if protected or v in versions and v not in seen else remove
   target.append(dict(x,family=family,version=list(v),protected=protected));seen.add(v)
 return {'keep':keep,'remove':remove,'unknown':unknown}

def collect_drive():
 items=[]
 for folder in sorted(FOLDERS):
  page=None
  while True:
   q={'q':f"'{folder}' in parents and trashed=false",'pageSize':1000,'fields':'nextPageToken,files(id,name,size,mimeType,parents,createdTime,webViewLink)'}
   if page:q['pageToken']=page
   result=api('https://www.googleapis.com/drive/v3/files?'+urllib.parse.urlencode(q));items+=result.get('files',[]);page=result.get('nextPageToken')
   if not page:break
 return items

def protections():
 s=json.loads((ROOT/'work/build-install/state.json').read_text());profiles=json.loads((ROOT/'work/build-profiles/profiles.json').read_text())
 ids=set(re.findall(r'(?:/d/|[?&]id=)([A-Za-z0-9_-]+)',json.dumps(s)))
 names={x['file'] for x in profiles.values() if isinstance(x,dict) and 'file' in x}
 for x in profiles.values():
  if isinstance(x,dict) and x.get('required_assets'):names.add(x['required_assets']['file'])
 # Stable manifest and every package it references are protected.
 manifest=json.loads((ROOT/'work/build-install/live-manifest.json').read_text())
 for release in manifest['releases']:
  for kind in ['gameplay','assets']:ids.update(re.findall(r'(?:/d/|[?&]id=)([A-Za-z0-9_-]+)',release[kind]['url']))
 versions={s.get('locked'),s.get('current_gameplay')}|{x.get('version') for x in profiles.values() if isinstance(x,dict)}
 return ids,names,versions

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--github',action='store_true');p.add_argument('--drive',action='store_true');p.add_argument('--max-github',type=int,default=6);a=p.parse_args()
 out=ROOT/'work/release-retention';out.mkdir(exist_ok=True);now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');ids,names,locked=protections();result={}
 if a.drive:
  result['drive']=plan_drive(collect_drive(),ids,names)
  (out/('plan-'+now+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  if a.apply:
   for x in result['drive']['remove']:
    fresh=api('https://www.googleapis.com/drive/v3/files/'+x['id']+'?fields=id,name,parents,trashed')
    if fresh['name']!=x['name'] or not FOLDERS.intersection(fresh.get('parents',[])):raise RuntimeError('Drive item changed; replan')
    # Re-read locks immediately before each mutation, to protect concurrent releases.
    current_ids,current_names,_=protections()
    if x['id'] in current_ids or x['name'] in current_names:continue
    api('https://www.googleapis.com/drive/v3/files/'+x['id'],'PATCH',{'trashed':True})
    with (out/'actions.jsonl').open('a') as f:f.write(json.dumps({'time':now,'drive_trashed':x})+'\n')
   result['drive']['verified_remaining']=plan_drive(collect_drive(),*protections()[:2])
 if a.github:
  releases=json.loads(subprocess.check_output([str(BA_GH),'release','list','--repo',REPO,'--limit','100','--json','tagName,name,isDraft,isPrerelease,publishedAt'],text=True))
  releases=[dict(r,tag_name=r['tagName']) for r in releases]
  recognized=[r for r in releases if re.fullmatch(r'v\d+\.\d+\.\d+-dev\.\d+',r['tag_name'])]
  latest={r['tag_name'] for r in sorted(recognized,key=lambda r:tuple(map(int,re.findall(r'\d+',r['tag_name']))),reverse=True)[:2]}
  keep=latest|{'v'+v for v in locked if v};remove=[r for r in recognized if r['tag_name'] not in keep]
  result['github']={'keep':sorted(keep),'remove':[{'tag':r['tag_name'],'id':r.get('id',r['tag_name'])} for r in remove],'deleted':[]}
  (out/('plan-'+now+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  if a.apply:
   for r in remove[:a.max_github]:
    _,_,live_locks=protections()
    if r['tag_name'] in {'v'+v for v in live_locks if v}:continue
    env=dict(os.environ,BA_RELEASE_REQUEST=REQUEST)
    run=subprocess.run([str(BA_GH),'release','delete',r['tag_name'],'--repo',REPO,'--cleanup-tag','--yes'],env=env,text=True,capture_output=True)
    if run.returncode:
     result['github']['deferred']=run.stderr[-1000:];break
    result['github']['deleted'].append(r['tag_name'])
    with (out/'actions.jsonl').open('a') as f:f.write(json.dumps({'time':now,'github_deleted_release':r})+'\n')
 (out/'latest.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:({'keep':len(v['keep']),'remove':len(v['remove']),'deleted':len(v.get('deleted',[])),'deferred':v.get('deferred')} ) for k,v in result.items()}))
if __name__=='__main__':main()
