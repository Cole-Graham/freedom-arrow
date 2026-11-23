"""Route the existing PLA test roster through a real China database country and five UI specs."""
import copy,json

def apply(R,effective,put):
    c=json.loads((R/'china-ui-contract.json').read_text());country=c['country'];why='China Arsenal UI prototype'
    assert country['Id'] not in effective['CountriesJson']
    put('CountriesJson',country['Id'],{k:v for k,v in country.items() if k!='Id'},why)
    template=copy.deepcopy(effective['SpecializationsJson'][17]);template.pop('Id')
    for spec in c['specs']:
        row={**template,'CountryId':country['Id'],'Name':'PLA '+spec['name'],'UIName':spec['name'],
             'UIDescription':spec['name'],'Icon':spec['icon'],'Illustration':'FA_CHINA_FLAG'}
        assert spec['id']==17 or spec['id'] not in effective['SpecializationsJson']
        put('SpecializationsJson',spec['id'],row,why)
    configs=json.loads((R/'pla-configurations-contract.json').read_text())
    sf={r['unit'] for r in configs if r['kind']=='special'}
    units={u for u,r in effective['Units'].items() if r['Name'].startswith('PLA ')}
    groups={}
    for uid in sorted(units):
        r=effective['Units'][uid]
        group=next((sid for key,sid in [('naval_units',20),('armored_units',18),('rocket_units',19)] if uid in c[key]),None)
        if group is None:group=17 if r['Type'] in (8,16) or r['Role']==100 or uid in sf else 21
        groups[uid]=group;put('Units',uid,{'CountryId':4},why)
    pools=[r for r in effective['SpecializationAvailabilitiesJson'].values() if r['SpecializationId']==17]
    assert all(r['UnitId'] in units for r in pools)
    for r in pools:put('SpecializationAvailabilitiesJson',r['Id'],{'SpecializationId':groups[r['UnitId']]},why)
    receipt={'country':4,'specs':c['specs'],'unit_specs':groups,'availability_rows':len(pools),
             'grouping':'provisional UI-only grouping','native_verified':False}
    (R/'source/UserData/FreedomArrow/china-ui.json').write_text(json.dumps(receipt,indent=2)+'\n')
