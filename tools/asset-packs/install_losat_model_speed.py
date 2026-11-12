"""Install the explicitly pinned live package and add LOSAT assets without resetting shared models."""
from pathlib import Path
import json,hashlib,zipfile,shutil,datetime,fcntl,importlib.util,subprocess,shlex
h=Path.home();g=h/'.local/share/Steam/steamapps/common/broken_arrow';profile_path=Path(__file__).resolve().parent/'profiles-install40.json';profiles=json.loads(profile_path.read_text());profile=profiles['live'];assets=profile['required_assets'];selector_path=h/'Games/FreedomArrow-Profiles/switch.py'
spec=importlib.util.spec_from_file_location('guarded_switch',selector_path);selector=importlib.util.module_from_spec(spec);spec.loader.exec_module(selector)
sha=selector.sha
with (h/'Games/FreedomArrow-Profiles/switch.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);selector.closed()
 check=selector.install(profile,g,h,check=True)
 archive=h/'Downloads'/assets['file'];assert sha(archive)==assets['sha256'],'Asset archive checksum mismatch'
 with zipfile.ZipFile(archive) as z:
  names=z.namelist();assert len(names)==len(set(names));assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names)
  meta=json.loads(z.read('UserData/FAAssets/manifest.json'));assert meta['version']=='0.1.14'
  for n,digest in meta['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==digest,n
  asset_map=json.loads(z.read('UserData/FAModels/models.json'));entry=asset_map[assets['model']];assert entry['file']=='m_losat_static.fam' and entry['battle']=='m_losat_lo_static.fam' and entry['align'] is False
  model_path=g/'UserData/FAModels/models.json';before_models=model_path.read_bytes();mapping=json.loads(before_models)
  # Keep every existing non-LOSAT entry, including approved newer model choices.
  merged=dict(mapping);merged[assets['model']]=entry
  payload={n:z.read(n) for n in names if n.startswith('UserData/FAModels/m_losat')};assert len(payload)==40
  assert all(hashlib.sha256(b).hexdigest()==meta['files'][n] for n,b in payload.items())
  for n,data in payload.items():
   if n.endswith('.fam'):assert data[:16]==b'FAM1\x01\x00\x00\x00\x04\x00\x00\x00root','Non-static mesh'

  for n,b in payload.items():assert not (g/n).exists() or sha(g/n)==hashlib.sha256(b).hexdigest(),('Unexpected preexisting LOSAT file',n)
  payload['UserData/FAModels/models.json']=(json.dumps(merged,indent=2)+'\n').encode()
  assets_path='UserData/FAAssets/manifest.json';installed_meta=json.loads((g/assets_path).read_text());installed_meta['version']='0.1.14';installed_meta.setdefault('models',{})[assets['model']]=entry;installed_meta.setdefault('files',{}).update({n:hashlib.sha256(b).hexdigest() for n,b in payload.items()});installed_meta.setdefault('notes',[]).append('LOSAT live install: added supplied model; all prior shared model mappings/files preserved.')
  for stem in ['m_losat','m_losat_lo']:
   for ext in ['.fam','.mat.json']:installed_meta['files'].pop('UserData/FAModels/'+stem+ext,None)
  payload[assets_path]=(json.dumps(installed_meta,indent=2)+'\n').encode()
  payload['UserData/FAAssets/losat-install.json']=(json.dumps({'archive':assets,'installed_for':profile['version'],'files':{n:hashlib.sha256(b).hexdigest() for n,b in payload.items()},'runtime_verified':False},indent=2)+'\n').encode()
 # Protect every existing model/music file outside the explicit additions and registry/metadata writes.
 retired={'UserData/FAModels/'+stem+ext for stem in ['m_losat','m_losat_lo'] for ext in ['.fam','.mat.json']}
 protected={str(p.relative_to(g)):sha(p) for folder in ['UserData/FAModels','UserData/FAMusic'] for p in (g/folder).rglob('*') if p.is_file() and str(p.relative_to(g)) not in payload and str(p.relative_to(g)) not in retired}
 for n in ['Mods/FAModels.dll','Mods/FAMusic.dll']:protected[n]=sha(g/n)
 b=h/'Games/BA-Backups'/('pre-losat-static-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));b.mkdir(parents=True);existing=[]
 for n in set(payload)|retired:
  if (g/n).is_file():dest=b/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(g/n,dest);existing.append(n)
 canonical=h/'Games/FreedomArrow-Profiles/profiles.json';old_profiles=canonical.read_bytes();(b/'profiles.json').write_bytes(old_profiles)
 restore='from pathlib import Path\nimport shutil\nb=Path('+repr(str(b))+');g=Path('+repr(str(g))+')\nfor n in '+repr(sorted(set(payload)|retired))+':\n p=g/n\n if n in '+repr(existing)+':\n  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/n,p)\n else:p.unlink(missing_ok=True)\nshutil.copy2(b/"profiles.json",Path('+repr(str(canonical))+'))\n'
 (b/'restore-assets.py').write_text(restore)
 with (h/'.agent-changes.log').open('a') as f:f.write(datetime.datetime.now().astimezone().isoformat()+' | BA Codex | LOSAT shared asset additions and current live alias; old models/music/infantry positions preserved | requested LOSAT model-map repair and displayed speeds | revert: python3 '+str(b/'restore-assets.py')+' (gameplay restore is logged separately)\n')
 core=None
 try:
  selector.closed();assert model_path.read_bytes()==before_models and canonical.read_bytes()==old_profiles,'State changed during preflight'
  for n,data in payload.items():p=g/n;p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.fatmp');temp.write_bytes(data);temp.replace(p)
  for n in retired:(g/n).unlink(missing_ok=True)
  selector.closed();core=selector.install(profile,g,h)
  canonical.write_text(json.dumps(profiles,indent=2)+'\n')
  undo_core=shlex.split(core['undo']);master='import subprocess\nfrom pathlib import Path\nsubprocess.run('+repr(undo_core)+',check=True)\nexec(compile(Path('+repr(str(b/'restore-assets.py'))+').read_text(),"restore-assets","exec"))\n';(b/'restore-all.py').write_text(master)
  for n,data in payload.items():assert sha(g/n)==hashlib.sha256(data).hexdigest(),n
  for n,digest in protected.items():assert sha(g/n)==digest,('Unrelated shared asset changed',n)
  current_models=json.loads(model_path.read_text());assert all(current_models[k]==v for k,v in mapping.items() if k!=assets['model'])
  manager=json.loads((g/'UserData/BAModManager/manifest.json').read_text());enabled=[p for p in manager['packages'] if p['enabled']];assert len(enabled)==1 and enabled[0]['info']['id']=='freedomarrow.gameplay' and enabled[0]['info']['version']==profile['version']
  for name in ['pla-build.json','pla-infantry-prototype.json','pla-package-manifest.json']:assert not (g/'UserData/FreedomArrow'/name).exists(),name
  # Read back actual installed LOSAT values and pool, rather than trusting the requested contract.
  constants=g/'UserData/FreedomArrow/constants';units=json.loads((constants/'units.json').read_text());wa=json.loads((constants/'weapon_ammunitions.json').read_text());ams=json.loads((constants/'ammunitions.json').read_text());pools=json.loads((constants/'specialization_availabilities.json').read_text());own_ammo=next(a for a in wa.values() if a and a.get('UnitId')==984);round=ams[str(own_ammo['AmmunitionId'])];own_pools=[p for p in pools.values() if p and p.get('UnitId')==984]
  assert units['984']['Cost']==200 and len(own_pools)==1 and own_pools[0]['SpecializationId']==6 and own_pools[0]['MaxAvailabilityXp0']==2
  prop=json.loads((constants/'unit_propulsions.json').read_text());mob=json.loads((constants/'mobility.json').read_text());own_mob=next(x for x in prop.values() if x and x.get('UnitId')==984);assert mob[str(own_mob['MobilityId'])]['MaxSpeedRoad']==50
  assert round['ArmorTargeted']==1 and round['PenetrationAtMinRange']==round['PenetrationAtGroundRange']==550 and round['Damage']==10 and abs(round['MaxSpeed']*3.6-1300)<.001 and abs(round['MuzzleVelocity']*3.6-1300)<.001 and own_ammo['Quantity']==12 and not round['CanBeIntercepted']
 except Exception:
  if core is not None:subprocess.run(shlex.split(core['undo']),check=True)
  exec(compile(restore,str(b/'restore-assets.py'),'exec'));raise
 result={'installed':profile['label'],'version':profile['version'],'core_sha256':profile['sha256'],'assets_source_sha256':assets['sha256'],'core_verified_hashes':core['verified_hashes'],'asset_archive_verified_hashes':len(meta['files']),'model_payload_files':40,'retired_attachment_files_removed':len(retired),'preserved_shared_files_verified':len(protected),'static_root_only':True,'model_mappings_before':len(mapping),'model_mappings_after':len(merged),'all_unrelated_model_entries_preserved':True,'PLA_TEST_enabled':False,'ActualArrow_enabled':False,'LOSAT':{'cost':200,'specialization':'Stryker','availability':2,'KE_penetration':550,'damage':round['Damage'],'missiles':own_ammo['Quantity'],'missile_speed_card':round['MaxSpeed']*3.6,'vehicle_speed':50},'game_running':False,'runtime_verified':False,'undo':'python3 '+str(b/'restore-all.py')}
 with (h/'.agent-changes.log').open('a') as f:f.write(datetime.datetime.now().astimezone().isoformat()+' | BA Codex | '+profile['label']+' live LOSAT model-map and speed repair installed; shared assets retained | requested installation | revert: '+result['undo']+'\n')
 (Path(__file__).resolve().parent/'install-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
