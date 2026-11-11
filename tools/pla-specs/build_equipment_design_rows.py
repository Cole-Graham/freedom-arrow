from pathlib import Path
import json
import argparse
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args();p=args.out;p.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parents[2];t=json.loads((r/'tools/pla-specs/effective-preview.json').read_text());catalogue=json.loads((r/'releases/0.6/source/UserData/FreedomArrow/pla-model-catalogue.json').read_text());models=json.loads((r/'releases/0.6/source/UserData/FAModels/models.json').read_text());bodies={v['unitId']:v for v in json.loads((r/'releases/0.6/source/UserData/FAModels/infantry-bodies.json').read_text())};units=t['Units'];specs={i:t['SpecializationsJson'][str(i)]['UIName'] for i in range(17,23)};pool={};source={}
for row in t['SpecializationAvailabilitiesJson'].values():
 if row['SpecializationId'] in specs:pool.setdefault(row['UnitId'],set()).add(row['SpecializationId'])
for e in catalogue['entries']:source.setdefault(e['unit'],[]).append(e)
classes={0:'Recon',1:'Infantry',2:'Vehicles',3:'Support',4:'Logistics',5:'Helicopters',6:'Aircraft'};order=['Recon','Infantry','Vehicles','Support','Logistics','Helicopters','Aircraft','Naval'];records=[]
assignment_path=r/'releases/0.6/source/UserData/FreedomArrow/pla-spec-assignments.json';implemented_recon={x['parent'] for x in json.loads(assignment_path.read_text())['recon_variants']} if assignment_path.exists() else set()
for uid,u in units.items():
 uid=int(uid)
 if u['CountryId']!=4 or not u['DisplayInArmory'] or u['Type']==2:continue
 ss=sorted(pool.get(uid,{22}));class_name='Naval' if u['Type']==32 else classes.get(u['CategoryType'],'Vehicles');mod=models.get(u['Name']);visual=('PLA body: '+bodies[uid]['lods'][0]) if uid in bodies else 'Custom: '+mod['file'] if mod else 'Native: '+u['ModelFileName'];es=source.get(uid,[]);donor=es[0]['parent'] if es else None
 note='Named prototype; donor statistics are not a final design.' if uid in catalogue['new_units'] else ''
 status='Stand-in' if uid in catalogue['new_units'] else 'Appearance test' if uid==901 or 985<=uid<=1009 else 'Existing draft'
 ammo='AT (current donor); DZT98 thermobaric (planned, not implemented)' if uid==1023 else ''
 role='PF-98 fire support team (planned design)' if uid==1023 else ''
 links='; '.join('row '+str(e['sheet_row']) for e in es)
 link='=HYPERLINK("#gid=501&range=B'+str(es[0]['sheet_row'])+'","'+links+'")' if es else ''
 parent=units.get(str(donor),{});donor_text=(str(donor)+' — '+parent.get('HUDName','')+'; current cost '+str(u['Cost'])) if donor else 'Current cost '+str(u['Cost'])+'; see source contract'
 records.append({'key':uid,'spec_ids':ss,'class':class_name,'values':[uid,u['HUDName'],specs[ss[0]],' | '.join(specs[i] for i in ss[1:]),class_name,visual,status,role,ammo,'','',note,link,donor_text]})
 # Record likely recon variants as plans, without adding speculative game definitions.
 if uid not in implemented_recon and u['Type']==8 and (u['Role']==73 or u['HUDName'] in ['Z-9WA','Z-19','Z-21']) and 'recon' not in u['HUDName'].lower():
  records.append({'key':'PLAN-'+str(uid)+'-RECON','spec_ids':ss,'class':'Recon','values':['PLAN-'+str(uid)+'-RECON',u['HUDName']+' Recon',specs[ss[0]],' | '.join(specs[i] for i in ss[1:]),'Recon',visual,'Planned','Recon gunship variant','','','','Planned role; not yet a game unit. Design optics, weapons and cost before implementation.',link,'Based on unit '+str(uid)]})
records.sort(key=lambda x:(x['spec_ids'][0],order.index(x['class']),str(x['values'][1]),str(x['key'])));assert len({str(x['key']) for x in records})==len(records)
headers=['Unit / plan ID','Unit name','Primary spec','Shared specs','Class','Current model / visual','Design status','Role / unit design','Munitions / loadouts','Desired cost','Stat changes','Design notes','Model list source','Current donor / baseline']
design=[headers]+[x['values'] for x in records];view=[['Spec','Class','Unit name','Unit / plan ID','Design status','Current model / visual','Edit unit design','Notes']]
for spec in range(17,23):
 for clas in order:
  for idx,x in enumerate(records,2):
   if spec not in x['spec_ids'] or clas!=x['class']:continue
   view.append([specs[spec],clas,"='PLA equipment designs'!B"+str(idx),x['key'],"='PLA equipment designs'!G"+str(idx),"='PLA equipment designs'!F"+str(idx),'=HYPERLINK("#gid=502&range=A'+str(idx)+'","Edit design")','Planned role, not in game' if str(x['key']).startswith('PLAN-') else 'Build 12 draft; shared ID means one game unit'])
(p/'design-rows.json').write_text(json.dumps(design,indent=2)+'\n');(p/'spec-view-rows.json').write_text(json.dumps(view,indent=2)+'\n');(p/'canonical-records.json').write_text(json.dumps(records,indent=2)+'\n');print({'canonical_records':len(records),'game_units':sum(isinstance(x['key'],int) for x in records),'planned_recon':sum(isinstance(x['key'],str) for x in records),'spec_view_rows':len(view)-1})
