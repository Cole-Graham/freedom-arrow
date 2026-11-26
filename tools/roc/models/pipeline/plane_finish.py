"""ROC planes get the French-preview Rafale/Mirage finish (Osama 26 Nov 14:4x "use the Rafale and mirage materials we have on the French preview
... apply it on all the planes", "vanilla f-16 glass transplant from vanilla for all the fighters").
- Fighters: canopy = cockpitDonor US_F16_Glass (clear glass as the fallback until the donor loads); glass UVs squeezed into the F-16 glass
  patch with model-rework-096/glassuv-1123/glassuv.py (no soap-film waves), in all 4 .fam files.
- Mirage 2000-5: same C5 FBX as the French Mirage (m_mirage2k, md5 1620dec6): its metal/roughness maps as the mask, used as painted
  (metallic 1 / smoothness 0, as m_mirage2k).
- F-16A / F-16V: the seller's specular map -> mask (R = A = normalised specular, G 1), Rafale ranges metal 0.35-0.45, smoothness 0.35-0.80.
- Planes without metal/gloss maps (F-5F, F-CK-1, C-130HE, Chung Hsiang II): the Rafale's mid values, metallic 0.40 / smoothness 0.55.
Originals are kept in veh/x/<slug>/pre-matfix/. usage: python plane_finish.py (pla-division venv)"""
import json,os,shutil,subprocess,numpy as np
from PIL import Image
H=os.path.dirname(os.path.abspath(__file__))+'/..';V=H+'/veh';M=V+'/models';W='/home/sam/tars/work/ba-dev/replicas/codex/work'
GUV=W+'/model-rework-096/glassuv-1123/glassuv.py';PY=W+'/pla-division/.venv/bin/python'
FIGHTERS=['f16a','f16v','f5f','fck1','mirage'];PLANES=FIGHTERS+['c130','chx2']
RAF=dict(metallicRemap=[0.35,0.45],smoothnessRemap=[0.35,0.8])
D6=H+'/dl6'
SPEC={('f16a',0):D6+'/F-16A/combat_jet_interior_specular.png',('f16a',4):D6+'/F-16A/combat_jet_interior_specular.png',
      ('f16a',1):D6+'/F-16A/combat_jet_alternative2_specular.png',('f16v',0):V+'/x/f16v/F16_Body_Spec.tga'}
def fams(s):return [f'm_roc_{s}_static',f'm_roc_{s}_lo_static',f'm_roc_{s}_lo_static_l1',f'm_roc_{s}_lo_static_l2']
def size(s,lvl,i):return Image.open(f'{M}/m_roc_{s}_{lvl}_tex{i}.png').size
def save_mask(s,i,mk):
    for lvl in ('static','lo_static'):
        Image.fromarray(mk).resize(size(s,lvl,i),Image.LANCZOS).save(f'{M}/m_roc_{s}_{lvl}_tex{i}_mask.png')
newmasks=[]
def spec_mask(s,i,f):
    L=np.asarray(Image.open(f).convert('L'),np.float32);lo,hi=np.percentile(L,2),np.percentile(L,98);a=np.clip((L-lo)/max(hi-lo,1),0,1)*255
    one=np.full_like(a,255);mk=np.stack([a,one,0*one,a],-1).round().astype(np.uint8);save_mask(s,i,mk);newmasks.append((s,i))
for s in PLANES:
    bk=f'{V}/x/{s}/pre-matfix';os.makedirs(bk,exist_ok=True)
    for st in fams(s):
        for ext in ('.fam','.mat.json'):
            if not os.path.exists(f'{bk}/{st}{ext}'):shutil.copy(f'{M}/{st}{ext}',bk)
    for lvl in ('static','lo_static'):
        for f in os.listdir(M):
            if f.startswith(f'm_roc_{s}_{lvl}_tex') and f.endswith('_mask.png') and not os.path.exists(f'{bk}/{f}'):shutil.copy(f'{M}/{f}',bk)
# masks
mt=lambda n:np.asarray(Image.open(f'{D6}/Mirage 2000/textures/Mirage2K/mr2k_{n}.png').convert('L'),np.float32)
met,rough=mt('Metallic'),mt('Roughness');one=np.full_like(met,255)
save_mask('mirage',0,np.stack([met,one,0*one,255-rough],-1).round().astype(np.uint8));newmasks.append(('mirage',0))
for (s,i),f in SPEC.items():spec_mask(s,i,f)
# material files
for s in PLANES:
    for st in fams(s)[:2]:
        p=f'{M}/{st}.mat.json';mj=json.load(open(f'{V}/x/{s}/pre-matfix/{st}.mat.json'))
        for k,v in list(mj.items()):
            if v.get('clearGlass'):
                if s in FIGHTERS:mj[k]={'cockpitDonor':'US_F16_Glass','fallback':v}
                continue
            if 'cockpitDonor' in v:continue
            i=int(k.split('_tex')[1].split('.')[0]) if '_tex' in k.split('|')[0] else None
            if s=='mirage' and i==0:v.update(metallic=1.0,smoothness=0.0);v.pop('metallicRemap',None);v.pop('smoothnessRemap',None)
            elif i is not None and os.path.exists(f'{M}/{st}_tex{i}_mask.png'):v.update(metallic=1.0,smoothness=0.0,**RAF)
            else:v.update(metallic=0.4,smoothness=0.55);v.pop('metallicRemap',None);v.pop('smoothnessRemap',None)
        json.dump(mj,open(p,'w'),indent=1)
    for l in ('l1','l2'):shutil.copy(f'{M}/m_roc_{s}_lo_static.mat.json',f'{M}/m_roc_{s}_lo_static_{l}.mat.json')
# glass UVs into the vanilla F-16 glass patch (always from the pre-matfix .fam, so a rerun does not squeeze twice)
tmp='/tmp/roc-glassuv';os.makedirs(tmp,exist_ok=True)
for s in FIGHTERS:
    for st in fams(s):
        mat=f'{M}/{st}.mat.json';src=f'{V}/x/{s}/pre-matfix/{st}.fam'
        out=subprocess.run([PY,GUV,mat,tmp,src],capture_output=True,text=True).stdout.strip();print(out.replace(tmp+'/',''))
        shutil.move(f'{tmp}/{st}.fam',f'{M}/{st}.fam')
lst=[f'm_roc_{s}_{lvl}_tex{i}_mask.png' for s,i in newmasks for lvl in ('static','lo_static')]
open(V+'/fat/list_matfix.txt','w').write('\n'.join(lst)+'\n')
for f in lst:
    if os.path.exists(f'{V}/fat/{f[:-4]}.fat'):os.makedirs(V+'/fat/old-matfix',exist_ok=True);shutil.move(f'{V}/fat/{f[:-4]}.fat',f'{V}/fat/old-matfix/{f[:-4]}.fat')
print('masks',lst)
