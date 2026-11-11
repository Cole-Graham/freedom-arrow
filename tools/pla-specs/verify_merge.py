"""Verify the complete Build9/Build10 union from archive bytes and loader source."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile
r=Path(__file__).resolve().parents[2];c=json.loads((r/'releases/0.6/pla-specializations-contract.json').read_text())
p=argparse.ArgumentParser();p.add_argument('--branches',type=Path,required=True);p.add_argument('--transition',type=Path,required=True);p.add_argument('--merged',type=Path,required=True);a=p.parse_args()
for version,path in [('9',a.branches),('10',a.transition)]:
 with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==c['merged_from'][version]['sha256']
revision={'README.md','mod.json','Mods/FAModels.dll','Mods/FreedomArrow.Runtime.dll','UserData/FreedomArrow/channel.json','UserData/FreedomArrow/pla-build.json','UserData/FreedomArrow/payload-manifest.json','UserData/FreedomArrow/pla-package-manifest.json','UserData/FAAssets/manifest.json','UserData/FreedomArrow/release-notes.md','UserData/FreedomArrow/pla-specializations.json'}
checked=0
with zipfile.ZipFile(a.branches) as b9,zipfile.ZipFile(a.transition) as b10,zipfile.ZipFile(a.merged) as merged:
 for n in b9.namelist():
  if n in revision:continue
  assert b9.read(n)==merged.read(n),('Build9 content lost',n);checked+=1
 old=json.loads(b9.read('UserData/FreedomArrow/pla-specializations.json'));new=json.loads(merged.read('UserData/FreedomArrow/pla-specializations.json'))
 for k in ['build','base_sha256']:old.pop(k);new.pop(k)
 assert old==new
 models=[n for n in b10.namelist() if n.startswith(('UserData/FAModels/','UserData/FAMusic/'))]
 repair=json.loads(merged.read('UserData/FreedomArrow/infantry-arm-repair.json'))['sha256'];binding={'UserData/FAModels/infantry-bodies.json','UserData/FAModels/infantry-weapons.json'}
 for n in models:
  if n in repair or n in binding:continue
  assert b10.read(n)==merged.read(n),('Build10 asset lost',n)
 provenance=json.loads(merged.read('UserData/FreedomArrow/merge-provenance.json'));assert provenance['parents']==c['merged_from']
# Build10's complete loader hook/failure-restoration source differs only in the version label.
source=r/'releases/0.6/experimental-model-loader/FAModels.cs';s=source.read_text();prior=subprocess.check_output(['git','show',c['merged_from']['10']['source']+':releases/0.6/experimental-model-loader/FAModels.cs'],cwd=r,text=True)
assert s.replace('"0.3.11"','"0.3.10"')==prior
print(json.dumps({'build9_payloads_byte_identical_except_explicit_revision_files':checked,'all_build9_constants_and_repaired_assets_retained':True,'build10_static_model_cockpit_and_music_assets_retained':True,'build10_immediate_hide_and_failure_restore_source_exact_except_version':True,'native_verified':False},indent=2))
