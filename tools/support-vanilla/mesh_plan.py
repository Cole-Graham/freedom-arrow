"""Support-tab armory meshes cut to the triangle count of the vanilla unit they stand in for (Osama 14 Nov 22:3x PST:
"estimate what vanilla has and pare it down"). Vanilla LOD0 counts: texture-audit-20261114/vanilla_tris_lod0.json."""
import json,zipfile,sys
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
V=json.load(open('/home/sam/tars/work/ba-dev/replicas/codex/work/texture-audit-20261114/vanilla_tris_lod0.json'))
REF={'phl':'RU_9K58_Smerch','grad':'RU_BM_21_Grad','df':'Iskander_Klub','hq9':'RU_S300PM','buk':'RU_BUKM2','tor':'RU_TOR','osa':'RU_AKM_OSA',
     'fk':'RU_DT30_PANTSIR','malva':'DLC3_2S43_Malva','m109':'US_M109A6','2s1':'RU_2S1','nona':'RU_NonaSVK','zsu':'RU_ZSU-2-4',
     'tung':'RU_Tunguska','lavad':'US_LAV_AD','deriv':'RU_Derivatsiya','kamaz':'DLC3_KamAZ6560'}
PICK={'m_phl03_static.fam':'phl','m_phl16_static.fam':'phl','m_phl191b_static.fam':'phl','m_phl191ch_static.fam':'phl','m_phl81.fam':'grad','sx2190.fam':'grad',
 'm_df15_static.fam':'df','m_df17_static.fam':'df','m_df21_static.fam':'df','m_df31a_static.fam':'df','m_yj18_static.fam':'df','m_hq22g_static.fam':'hq9',
 'm_hq11_static.fam':'buk','m_hq12_static.fam':'buk','m_hq16_static.fam':'buk','m_hq6a_static.fam':'buk','m_hq17a_static.fam':'tor','m_hq7g_static.fam':'osa',
 'm_fk2000s_static.fam':'fk','m_pcl181_static.fam':'malva','m_pcl09_static.fam':'malva','m_plz83_static.fam':'malva','m_plz05_static.fam':'m109',
 'm_plz45a4_static.fam':'m109','m_sh16_static.fam':'m109','m_plz07_static.fam':'2s1','m_plz70_static.fam':'2s1','m_plz85_static.fam':'2s1',
 'm_plz89_static.fam':'2s1','pll05_static.fam':'nona','m_pll09_static.fam':'nona','m_pgz04a_static.fam':'zsu','m_pgz88_static.fam':'zsu',
 'm_pgz95b_static.fam':'zsu','m_pgz09_static.fam':'tung','m_pgl625_static.fam':'lavad','m_jrvg1_static.fam':'deriv','m_sx2220.fam':'kamaz'}
z=zipfile.ZipFile('/home/sam/tars/work/ba-dev/replicas/codex/work/pla-hotfix39-worktree/releases/0.6/out/0.8/FreedomArrow-0.9.0-dev.8-complete.bamod')
jobs=[]
for f,k in PICK.items():
    open('/tmp/_p.fam','wb').write(z.read('UserData/FAModels/'+f));n=sum(len(s['idx'])//3 for _,ss in read_fam('/tmp/_p.fam') for s in ss)
    tgt=V[REF[k]];jobs.append({'file':f,'now':n,'vanilla':REF[k],'target':tgt,'cut':n>tgt*1.1})
    print('%-24s now %7d  vanilla %-16s %7d  %s'%(f,n,REF[k],tgt,'CUT' if n>tgt*1.1 else 'ok'))
json.dump(jobs,open('jobs.json','w'),indent=1);print('to cut',sum(j['cut'] for j in jobs),'of',len(jobs))
