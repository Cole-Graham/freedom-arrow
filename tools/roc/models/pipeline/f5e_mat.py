"""F-5E material files (Shawn 27 Nov 19:4x: "treatment of glass and PBR of hull is consistent with other planes"): as plane_finish.py does for
the planes without metal/gloss maps (F-5F, F-CK-1): painted parts metallic 0.40 / smoothness 0.55; canopy = cockpitDonor US_F16_Glass with
clear glass as the fallback, its UVs squeezed into the vanilla F-16 glass patch (glassuv.py). Steel, tyres and the green HUD keep their own
values. (glass.py had read the old F-5F GLB and marked the wrong maps as glass; this rewrites both files.) usage: python f5e_mat.py"""
import json,os,shutil,subprocess
H=os.path.dirname(os.path.abspath(__file__))+'/..';M=H+'/veh/models';W='/home/sam/tars/work/ba-dev/replicas/codex/work'
GUV=W+'/model-rework-096/glassuv-1123/glassuv.py';PY=W+'/pla-division/.venv/bin/python'
GLASS='|0.8500,0.9000,0.9500,0.1500';FB={'metallic':0.0,'smoothness':0.95,'alpha':'BLEND','cutoff':0.5,'emissive':[0,0,0],'unlit':False,'clearGlass':True,'opacity':0.1}
for st in ('m_roc_f5f_static','m_roc_f5f_lo_static'):
    p=f'{M}/{st}.mat.json';mj=json.load(open(p))
    for k,v in mj.items():
        if k==GLASS:mj[k]={'cockpitDonor':'US_F16_Glass','fallback':FB};continue
        if k.startswith('|'):continue      # steel, tyre, HUD
        for x in ('clearGlass','opacity'):v.pop(x,None)
        v.update(alpha='OPAQUE',metallic=0.4,smoothness=0.55)
    json.dump(mj,open(p,'w'),indent=1)
for l in ('l1','l2'):shutil.copy(f'{M}/m_roc_f5f_lo_static.mat.json',f'{M}/m_roc_f5f_lo_static_{l}.mat.json')
tmp='/tmp/roc-glassuv-f5e';os.makedirs(tmp,exist_ok=True)
for st in ('m_roc_f5f_static','m_roc_f5f_lo_static','m_roc_f5f_lo_static_l1','m_roc_f5f_lo_static_l2'):
    out=subprocess.run([PY,GUV,f'{M}/{st}.mat.json',tmp,f'{M}/{st}.fam'],capture_output=True,text=True);print(out.stdout.strip()[-200:],out.stderr.strip()[-200:])
    shutil.move(f'{tmp}/{st}.fam',f'{M}/{st}.fam')
