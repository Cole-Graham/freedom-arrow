"""Display policy: named SF keep central emblems; specialist teams show their weapon."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];path=root/'tools/pla-specs/infantry-identity-contract.json';c=json.loads(path.read_text());designer=json.loads((root.parent/'pla-infantry-insignia-build19/releases/0.6/source/UserData/FreedomArrow/pla-infantry-designer.json').read_text());native_path=root.parent/'black-widow-turn-20261110/vanilla/Units.json';native={u['Id']:u for u in json.loads(native_path.read_text())};decisions=[]
for e in designer['entries']:
 r=c['units'][str(e['unit'])];name=r['display_name'];lo=name.lower();donor=None;custom=None;why=None
 if r['identity_type']=='named formation':r['icon_kind']='sf_emblem';continue
 if 'qlu-11' in lo:custom='QLU11';why='Owned QLU11 side contour for precision-grenade weapon team'
 elif 'qts recon cell' in lo:custom='QTS11';why='Owned QTS11 side contour for test specialty cell'
 elif 'hmg' in lo or 'qjz-' in lo:donor=400;why='Tripod heavy machine-gun team icon'
 elif 'qlz-' in lo or any(x in lo for x in ['lg3','lg4','lg5','lg6']):donor=112;why='Closest native automatic-grenade weapon-team icon'
 elif 'hn-6' in lo or 'qw-2' in lo or 'air-defense scouts' in lo:donor=120;why='Shoulder-fired MANPADS weapon-team icon'
 elif 'hj-12' in lo or 'hj-12e' in lo or any(x in lo for x in ['gam-102','tl-4']):donor=408;why='Portable modern ATGM weapon-team icon'
 elif 'caat' in lo:donor=66;why='Mixed MG/AT weapon-team icon for the existing mixed CAAT design'
 elif 'hj-8' in lo or 'qn-202' in lo or 'guided-at' in lo:donor=121;why='Tripod ATGM weapon-team icon'
 elif 'hj-73' in lo or 'malyutka' in lo:donor=128;why='Native light ATGM team icon; Chinese launcher geometry remains a stand-in'
 elif 'pf-98' in lo:donor=63;why='Recoilless/shoulder-launcher fire-support team icon'
 elif 'thermobaric' in lo or 'fhj-02' in lo:donor=122;why='Native incendiary/thermobaric tube-team icon; not exact FHJ02 seven-tube geometry'
 elif 'sniper' in lo:donor=333;why='Sniper/anti-materiel rifle team icon'
 elif 'gpmg' in lo:donor=399;why='General-purpose machine-gun team icon'
 elif 'engineer' in lo:donor=117;why='Native assault-engineer weapon/equipment icon'
 elif 'smg assault' in lo:donor=409;why='Native close-assault weapon icon'
 elif 'suppressed scouts' in lo:donor=65;why='Native scout weapon/equipment icon'
 elif 'observer' in lo:donor=65;why='Native scout/observation equipment icon'
 else:r['icon_kind']='branch_insignia';continue
 r['icon_kind']='weapon_team'
 if custom:
  r.update(profile='WPN_'+custom,address='FA_PLA_INF_WPN_'+custom,art_source='Approved installed '+custom+' mesh contour',art_basis=why,native_donor_unit=None)
 else:
  r.update(profile=None,address=native[donor]['ThumbnailFileName'],art_source='Vanilla Units row '+str(donor)+' '+native[donor]['HUDName'],art_basis=why+'; reused native artwork, not an exact Chinese drawing',native_donor_unit=donor)
 decisions.append({'unit':e['unit'],'name':name,'address':r['address'],'basis':why,'native_donor_unit':donor})
c['profiles']=sorted({r['profile'] for r in c['units'].values() if r['profile']});c['weapon_team_policy']={'native_units_sha256':hashlib.sha256(native_path.read_bytes()).hexdigest(),'named_sf_emblems_take_priority':True,'named_sf_wreaths_removed':True,'decisions':decisions};path.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n');print('Weapon/equipment icons:',len(decisions),'Named SF emblems:',sum(r.get('icon_kind')=='sf_emblem' for r in c['units'].values()),'Other branch badges:',sum(r.get('icon_kind')=='branch_insignia' for r in c['units'].values()))
