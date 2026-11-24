"""Build every FA scenario. Map-specific data lives in sibling modules; each map's size and ranked pool live in ../maps.json."""
from pathlib import Path
import argparse, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import highway_2v2, chkalovsk_2v2, dead_center_1v1, dead_center_2v2, airport_4v4, baltiisk_3v3, dam_3v3, oil_rush_4v4, cold_harbor_4v4, kadaga_1v1, klaipeda_1v1, jelgava_1v1, chernyakhovsky_1v1, bay_of_winds_3v3, coal_mountain_2v2, pve
MAPS=(dead_center_2v2, dead_center_1v1, chkalovsk_2v2, highway_2v2, airport_4v4, baltiisk_3v3, dam_3v3, oil_rush_4v4, cold_harbor_4v4, kadaga_1v1, klaipeda_1v1, jelgava_1v1, chernyakhovsky_1v1, bay_of_winds_3v3, coal_mountain_2v2)
SIZES=('1v1','2v2','3v3','4v4')
# Written next to the scenario folders; package.py ships it as UserData/FreedomArrow/maps.json (the game and the ranked hub read it).
REGISTRY_OUT='_maps.json'
def registry(out):
    """Lateralus 23 Nov 2026: map size from data, not from the [NvN] tag. Check every built map against maps.json and list the exact
    names and IDs for the game and the hub."""
    src=json.loads((Path(__file__).resolve().parent.parent/'maps.json').read_text())['maps']
    ids=[m.__name__ for m in MAPS]
    assert sorted(ids)==sorted(src),('maps.json and make_scenario.py list different maps',sorted(set(ids)^set(src)))
    rows=[]
    for m in MAPS:
        e=src[m.__name__];assert e['size'] in SIZES,(m.__name__,e['size'])
        for name,skirmish in ((m.NAME,False),(m.SKIRMISH_NAME,True)):
            assert name.startswith(f"[FA] [{e['size']}] {e['base']} "),(m.__name__,name,'name tag/base must match maps.json',e)
            meta=json.loads((out/name/'meta.json').read_text())
            assert meta['scenario']==name,(name,meta['scenario'])
            rows.append(dict(id=m.__name__,name=name,guid=meta['guid'],size=e['size'],base=e['base'],ranked=bool(e['ranked']) and not skirmish,skirmish=skirmish))
    for name in pve.ALL_NAMES:
        meta=json.loads((out/name/'meta.json').read_text())
        rows.append(dict(id='pve',name=name,guid=meta['guid'],size='PvE',base='',ranked=False,skirmish='Skirmish' in name))
    built={p.name for p in out.iterdir() if p.is_dir()}
    assert built=={r['name'] for r in rows},('built scenarios missing from maps.json',sorted(built^{r['name'] for r in rows}))
    for s in SIZES:assert any(r['ranked'] and r['size']==s for r in rows),('no ranked map for',s)
    # A joining client with no local scenario name finds its map by the exact set of zone IDs (conquest Settings.ResolveMap). Online maps
    # that share a set must have the same zone values (the PvE copies share their base map's), so a new map cannot reuse another's IDs.
    W=json.loads((Path(__file__).resolve().parent.parent/'source/UserData/FAConquestPrototype/settings.json').read_text())['MapZoneWeights'];by={}
    for r in rows:
        if not r['skirmish']:by.setdefault(frozenset(W[r['name']]),[]).append(r['name'])
    for names in by.values():assert len({json.dumps(W[n],sort_keys=True) for n in names})==1,('online maps with the same zone IDs and different values',names)
    (out/REGISTRY_OUT).write_text(json.dumps(dict(version=1,maps=rows),indent=1,ensure_ascii=False)+'\n')
    print('maps.json:',len(rows),'scenarios;',{s:sorted(r['base'] for r in rows if r['ranked'] and r['size']==s) for s in SIZES})
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    for mod in (*MAPS,pve):mod.build(a.game_dir,a.out)
    registry(a.out)
if __name__=='__main__':main()
