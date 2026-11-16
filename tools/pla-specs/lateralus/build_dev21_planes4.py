"""Lateralus plane sale test build on Osama's latest dev build (Lateralus 16 Nov 2026 ~04:12 PST, thread 1571554273639006392:
"Yes add the log line on a test build, built on top of the latest dev build from Osama"). dev.21 + plane sale (planes3 rules/HUD) +
server points overwrite log. Identity files are restored afterwards; the batch branch stays at dev.21 identity."""
from pathlib import Path
import json,os,re,shutil,subprocess
ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/missile-hp-repo');REL=ROOT/'releases/0.6';SRC=REL/'source';FA=SRC/'UserData/FreedomArrow'
PREV='0.9.0-dev.21';V=PREV+'-planes4';BUILD=194
SHARED=Path('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/local-dev21')
base=SHARED/f'FreedomArrow-{PREV}-complete.bamod'
PY='/home/sam/tars/work/ba-dev/replicas/codex/work/freedom-arrow/.venv/bin/python'
DOTNET='/nix/store/d5l0ayis8vlll18v1wp9k9cxqydv2dxk-dotnet-sdk-wrapped-8.0.421/bin/dotnet'
ZIP='/nix/store/2562wqrkss8xv8z2blaa4cvgg2yknlkq-zip-3.0/bin/zip'
GAME='/home/sam/tars/work/ba-dev/replicas/codex/work/game-1.2.2.1'
IDENTITY=['releases/0.6/mod.json','releases/0.6/source/UserData/FreedomArrow/channel.json','releases/0.6/source/UserData/FreedomArrow/pla-build.json',
 'releases/0.6/source/runtime-qa/Runtime.cs','releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj']
enc=lambda d:json.dumps(d,indent=2,ensure_ascii=False)+'\n'
def edit(p,old,new):
    s=p.read_text();assert s.count(old)==1,(p,old);p.write_text(s.replace(old,new))
(REL/'out/0.8').mkdir(parents=True,exist_ok=True)
rc=REL/f'out/0.8/FreedomArrow-{PREV}.json'
if not rc.exists():shutil.copy2(SHARED/f'FreedomArrow-{PREV}.json',rc)
PR=FA/'plane-refund.json'
try:
    PR.write_text(enc({'Category':6,'MaximumRefundPercent':100.0,'MinimumRefundPercent':20.0,'HealthCostMultiplier':0.0,'SupplyMultiplier':0.0,
        'RefundMultiplier':1.0,'PayoutSeconds':300.0,'HudIcon':'US_F15C-Label',
        'note':'Aircrafts deck tab only (UnitCategoryType 6). Engine refund settings swapped in for that unit\'s RefundUnit call; vanilla 90 / 20 / 0.5 / 0.04 x / 1.0. Payout spread evenly over PayoutSeconds of game time.',
        'source':'Lateralus 15 Nov 2026 14:24-15:42 PST, thread 1571554273639006392 (test build only)'}))
    m=json.loads((REL/'mod.json').read_text());assert m['version']==PREV
    m['version']=V;m['description']=f'{V}: TEST BUILD for Lateralus, {PREV} plus: sold Aircrafts-tab planes refund 100% (engine formula, max 100%, no damage/ammo deduction) paid over 5 minutes with an F-15C +N/min HUD line; every server points overwrite is logged (server_money_set). '+m['description']
    (REL/'mod.json').write_text(enc(m))
    c=json.loads((FA/'channel.json').read_text());c['package_version']=V;(FA/'channel.json').write_text(enc(c))
    b=json.loads((FA/'pla-build.json').read_text());b.update(build=BUILD,label='Freedom Arrow '+V);(FA/'pla-build.json').write_text(enc(b))
    edit(SRC/'runtime-qa/Runtime.cs',f'"Freedom Arrow", "{PREV}"',f'"Freedom Arrow", "{V}"')
    edit(SRC/'runtime-qa/FreedomArrow.Runtime.csproj',f'<Version>{PREV}</Version>',f'<Version>{V}</Version>')
    (FA/f'pla-{V}.json').write_text(enc({'version':V,'base':PREV,'build':BUILD,'plane_refund':json.loads(PR.read_text()),
        'server_money_log':'NetworkUserRoomStateHandler.OnClientGetMoney prefix/postfix: server_money_set (before/after points), server_money_watch every 60 s',
        'verified':'build checks only; not yet seen in a game'}))
    subprocess.run([DOTNET,'build','-c','Release',f'-p:GameDir={GAME}'],cwd=SRC/'runtime-qa',check=True,env={**os.environ,'DOTNET_CLI_TELEMETRY_OPTOUT':'1'})
    subprocess.run([PY,str(ROOT/'tools/pla-specs/package_0_8_next.py'),'--prev',PREV,'--version',V,'--build',str(BUILD),
        '--base',str(base),'--outdir',str(REL/'out/0.8'),'--zip',ZIP],cwd=REL,check=True,
        env={**os.environ,'BA_DEVPOST_SKIP':'Lateralus plane sale test build, not a dev build'})
finally:
    subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True);PR.unlink(missing_ok=True)
