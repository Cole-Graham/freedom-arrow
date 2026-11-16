"""Lateralus test build (16 Nov 2026 ~06:00 PST, thread 1571554273639006392, "give me a test build"): 0.9.0-dev.24 + InterceptLead
rename and attach retry + SEAD bursts of 2 (sead_burst.py). Identity files are restored and the written constants removed afterwards."""
from pathlib import Path
import json,os,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3];REL=ROOT/'releases/0.6';SRC=REL/'source';FA=SRC/'UserData/FreedomArrow'
sys.path[:0]=[str(ROOT),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
import sead_burst,spaag_sead_data
PREV='0.9.0-dev.24';V=PREV+'-sead3';BUILD=197   # sead2: + the SPAAG/SAM data missing from dev.13-dev.24; sead3: + altitude intent arrow
SHARED=ROOT.parent/'pla-hotfix39-worktree/releases/0.6/out/local-dev24';base=SHARED/f'FreedomArrow-{PREV}-complete.bamod'
VAN=ROOT.parent/'lateralus-infantry-20261110/vanilla'
PY='/home/sam/tars/work/ba-dev/replicas/codex/work/freedom-arrow/.venv/bin/python'
DOTNET='/nix/store/d5l0ayis8vlll18v1wp9k9cxqydv2dxk-dotnet-sdk-wrapped-8.0.421/bin/dotnet'
ZIP='/nix/store/2562wqrkss8xv8z2blaa4cvgg2yknlkq-zip-3.0/bin/zip'
GAME=str(ROOT.parent/'game-1.2.2.1')
IDENTITY=['releases/0.6/mod.json','releases/0.6/source/UserData/FreedomArrow/channel.json','releases/0.6/source/UserData/FreedomArrow/pla-build.json',
 'releases/0.6/source/runtime-qa/Runtime.cs','releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj']
enc=lambda d:json.dumps(d,indent=2,ensure_ascii=False)+'\n'
def edit(p,old,new):
    s=p.read_text();assert s.count(old)==1,(p,old);p.write_text(s.replace(old,new))
(REL/'out/0.8').mkdir(parents=True,exist_ok=True)
rc=REL/f'out/0.8/FreedomArrow-{PREV}.json'
if not rc.exists():shutil.copy2(SHARED/f'FreedomArrow-{PREV}.json',rc)
CON=FA/'constants';assert not CON.exists(),'constants folder already present; refusing to overwrite'
z=zipfile.ZipFile(base);t={};patches={};n=[0]
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((VAN/(tab+'.json')).read_text())};patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
def put(tab,i,f):t[tab][i].update(f);patches[tab].setdefault(str(i),{}).update(f)
def ok(c,l):
    assert c,l;n[0]+=1
rec=sead_burst.apply(t,put,ok);rec2=spaag_sead_data.apply(t,put,ok)
try:
    CON.mkdir(parents=True);wn='UserData/FreedomArrow/constants/'+FIELD_TO_FILE['WeaponsJson']
    for tab in ('WeaponsJson','AmmunitionsJson'):
        wn='UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab]
        (SRC/wn).write_bytes((json.dumps(patches[tab],indent=2,ensure_ascii=z.read(wn).isascii())+'\n').encode())
    m=json.loads((REL/'mod.json').read_text());assert m['version']==PREV
    m['version']=V;m['description']=f'{V}: TEST BUILD for Lateralus, {PREV} plus: the Lateralus SPAAG/SAM vs SEAD data (bursts, gun damage, SAM pauses; missing from dev.13-dev.24), SEAD missiles (planes and helicopters) fire in bursts of 2, 1.0 s apart; own planes show a yellow altitude arrow (down or up) while an altitude change is ordered; the missile-defence gun lead correction is renamed Intercept Lead (logs intercept_lead_*) and retries its hook if Windows refuses it at startup. '+m['description']
    (REL/'mod.json').write_text(enc(m))
    c=json.loads((FA/'channel.json').read_text());c['package_version']=V;(FA/'channel.json').write_text(enc(c))
    b=json.loads((FA/'pla-build.json').read_text());b.update(build=BUILD,label='Freedom Arrow '+V);(FA/'pla-build.json').write_text(enc(b))
    edit(SRC/'runtime-qa/Runtime.cs',f'"Freedom Arrow", "{PREV}"',f'"Freedom Arrow", "{V}"')
    edit(SRC/'runtime-qa/FreedomArrow.Runtime.csproj',f'<Version>{PREV}</Version>',f'<Version>{V}</Version>')
    (FA/f'pla-{V}.json').write_text(enc({'version':V,'base':PREV,'build':BUILD,'sead_burst':rec,'spaag_sead_data':rec2,'sead_checks':n[0],
        'intercept_lead':'CramPrediction renamed InterceptLead; native attach retried at 5/15/30/60 s after a failure',
        'verified':'build checks only; not yet seen in a game'}))
    subprocess.run([DOTNET,'build','-c','Release',f'-p:GameDir={GAME}'],cwd=SRC/'runtime-qa',check=True,env={**os.environ,'DOTNET_CLI_TELEMETRY_OPTOUT':'1'})
    subprocess.run([PY,str(ROOT/'tools/pla-specs/package_0_8_next.py'),'--prev',PREV,'--version',V,'--build',str(BUILD),
        '--base',str(base),'--outdir',str(REL/'out/0.8'),'--zip',ZIP],cwd=REL,check=True,
        env={**os.environ,'BA_DEVPOST_SKIP':'Lateralus SEAD/intercept-lead test build, not a dev build'})
finally:
    subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True);shutil.rmtree(CON,ignore_errors=True)
