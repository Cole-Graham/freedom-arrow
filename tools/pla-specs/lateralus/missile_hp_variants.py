"""Interceptable missile HP test builds over exact 0.9.0-dev.12 (Lateralus, 15 Nov 2026, thread 1571554273639006392:
"give me three test builds that set the HP of all interceptables to 5, 7, and 9").

Each variant is dev.12 plus releases/0.6/source/runtime-qa/ProjectileHealth.cs reading UserData/FreedomArrow/projectile-health.json.
Nothing else differs. For each HP: write the identity files, build the runtime, run package_0_8_next.py. The identity files go
back to dev.12 at the end (the branch stays at dev.12 plus the hook); the per-variant receipts are kept.
Usage: missile_hp_variants.py 5 7 9
       missile_hp_variants.py 7 --burst-pause   (0.9.0-dev.12-hp7-burst: also the SPAAG burst pause below)
       missile_hp_variants.py 7 --burst-pause --lead-log   (0.9.0-dev.12-hp7-burst-lead: same, named for the full CramPrediction lead log)

--burst-pause (Lateralus 15 Nov 2026 09:01 PST: "Yes shorten the burst, and also add the sideways aim error log... just give me a
test build with these fixes and hp7"). In his hp7 run the gun spent its burst on missile 1 of a 2-missile salvo and sat in its
1.5-3.0 s pause while missile 2 (1.5-1.8 s behind) hit it. The 12 ground SPAAG guns whose rounds can hit SEAD missiles get
TimeBetweenBursts 0.8-1.0 s; burst length and the time between shots stay. Ship CIWS 706 and the AH-64 M230LF 40 are left alone.
"""
from pathlib import Path
import json,os,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3];REL=ROOT/'releases/0.6';SRC=REL/'source';FA=SRC/'UserData/FreedomArrow'
PREV='0.9.0-dev.12';BUILD=186
ZIP='/nix/store/2562wqrkss8xv8z2blaa4cvgg2yknlkq-zip-3.0/bin/zip'
PY='/home/sam/tars/work/ba-dev/replicas/codex/work/freedom-arrow/.venv/bin/python'   # has pycryptodome for the map builder
DOTNET='/nix/store/d5l0ayis8vlll18v1wp9k9cxqydv2dxk-dotnet-sdk-wrapped-8.0.421/bin/dotnet'
IDENTITY=['releases/0.6/mod.json','releases/0.6/source/UserData/FreedomArrow/channel.json','releases/0.6/source/UserData/FreedomArrow/pla-build.json',
 'releases/0.6/source/runtime-qa/Runtime.cs','releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj']
enc=lambda d:(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def edit(p,old,new):
    s=p.read_text();assert s.count(old)==1,(p,old);p.write_text(s.replace(old,new))
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod';assert base.exists(),base
BURST=[19,261,309,327,345,2009181,2009365,2009555,2009599,2010639,2010659,2010673];PAUSE=(0.8,1.0)
burst='--burst-pause' in sys.argv;lead='--lead-log' in sys.argv;CONST=FA/'constants/weapons.json'
def burst_pause():
    w=json.loads(zipfile.ZipFile(base).read('UserData/FreedomArrow/constants/weapons.json'));changed={}
    for i in BURST:
        r=w.setdefault(str(i),{});changed[i]=[r.get('TimeBetweenBurstsMin'),r.get('TimeBetweenBurstsMax')]
        assert changed[i][0] is None or changed[i][0]>=1.5,(i,changed[i])
        r.update(TimeBetweenBurstsMin=PAUSE[0],TimeBetweenBurstsMax=PAUSE[1])
    CONST.parent.mkdir(exist_ok=True);CONST.write_text(json.dumps(w,indent=2,ensure_ascii=False)+'\n');return changed
try:
    for hp in [int(x) for x in sys.argv[1:] if x.isdigit()]:
        V=f'{PREV}-hp{hp}'+('-burst' if burst else '')+('-lead' if lead else '')
        before=burst_pause() if burst else None
        (FA/'projectile-health.json').write_text(enc({'health':float(hp),'vanilla':1.0,'scope':'every CanBeTargeted projectile (MakeShellTargetable)',
            'source':'Lateralus 15 Nov 2026, thread 1571554273639006392'}))
        m=json.loads((REL/'mod.json').read_text());assert m['version']==PREV
        m['version']=V;m['description']=re.sub(r'^(Freedom Arrow 0\.9: China \(PLA\) on the full 0\.7\.0-dev\.58 game\. )',
            rf'\g<1>{V}: TEST BUILD, dev.12 with every interceptable missile at {hp} HP (vanilla 1)'+(', SPAAG burst pause 0.8-1.0 s, turret aim error in the AA log' if burst else '')+(', full gun lead-correction log' if lead else '')+'; ',m['description']);assert V in m['description']
        (REL/'mod.json').write_text(enc(m))
        c=json.loads((FA/'channel.json').read_text());c['package_version']=V;(FA/'channel.json').write_text(enc(c))
        b=json.loads((FA/'pla-build.json').read_text());b.update(build=BUILD,label='Freedom Arrow '+V);(FA/'pla-build.json').write_text(enc(b))
        edit(SRC/'runtime-qa/Runtime.cs','"Freedom Arrow", "0.9.0-dev.12"',f'"Freedom Arrow", "{V}"')
        edit(SRC/'runtime-qa/FreedomArrow.Runtime.csproj','<Version>0.9.0-dev.12</Version>',f'<Version>{V}</Version>')
        (FA/f'pla-{V}.json').write_text(enc({'version':V,'base':PREV,'build':BUILD,'projectile_health':float(hp),'vanilla_health':1.0,
            'hook':'ProjectileSpawnerHelper.MakeShellTargetable postfix (RVA 0x7DF1E0) writes _health, MaxHealth, HalfHealth',
            'data_changes':{'weapons':{str(i):{'TimeBetweenBursts_patch_before':before[i],'after':list(PAUSE)} for i in BURST}} if burst else 'none','verified':'build checks only; not yet seen in a game'}))
        subprocess.run([DOTNET,'build','-c','Release','-p:GameDir=/home/sam/tars/work/ba-dev/game'],cwd=SRC/'runtime-qa',check=True,
            env={**os.environ,'DOTNET_CLI_TELEMETRY_OPTOUT':'1'})
        subprocess.run([PY,str(ROOT/'tools/pla-specs/package_0_8_next.py'),'--prev',PREV,'--version',V,'--build',str(BUILD),
            '--base',str(base),'--outdir',str(REL/'out/0.8'),'--zip',ZIP],check=True,env={**os.environ,'BA_DEVPOST_SKIP':'Lateralus missile HP test build, not a dev build'})
        subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True)
finally:
    subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True);(FA/'projectile-health.json').unlink(missing_ok=True);CONST.unlink(missing_ok=True)
