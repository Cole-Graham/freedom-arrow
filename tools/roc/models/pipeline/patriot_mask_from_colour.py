"""Patriot-like surface for a ROC truck with no metal/gloss maps (Thunderbolt-2000, Shawn 27 Nov 20:0x): a _mask from the colour map -
metal 0.05 on paint, 0.55 on bright unpainted grey (low saturation, light: exhausts, hinges, worn steel), smoothness 0.24-0.46 (darker =
dirtier = rougher), AO 1; the .mat.json entry switches to the mask (metallic 1 / smoothness 0, as the other ROC trucks).
usage: python patriot_mask_from_colour.py SLUG TEXINDEX [TEXINDEX ...]"""
import sys,os,json,glob,shutil,numpy as np
from PIL import Image
slug,tis=sys.argv[1],[int(x) for x in sys.argv[2:]];V=os.path.dirname(os.path.abspath(__file__))+'/../veh';M=V+'/models';BK=f'{V}/x/{slug}/pre-patriot-pbr';os.makedirs(BK,exist_ok=True)
for lvl in ('static','lo_static'):
    for ti in tis:
        st=f'{M}/m_roc_{slug}_{lvl}_tex{ti}';c=np.asarray(Image.open(st+'.png').convert('RGB')).astype(np.float32)/255
        mx,mn=c.max(2),c.min(2);sat=(mx-mn)/np.maximum(mx,1e-3);L=c.mean(2)
        bare=np.clip((0.25-sat)/0.1,0,1)*np.clip((L-0.6)/0.15,0,1)
        metal=0.05+0.5*bare;smooth=0.24+0.22*np.clip(L/0.7,0,1)
        m=np.dstack([metal,np.ones_like(L),np.zeros_like(L),smooth]);Image.fromarray((m*255+0.5).astype(np.uint8),'RGBA').save(st+'_mask.png')
        print(os.path.basename(st),'bare %.1f%%'%(100*(bare>0.5).mean()),'smooth mean %.2f'%smooth.mean())
for f in glob.glob(f'{M}/m_roc_{slug}_*static*.mat.json'):
    if not os.path.exists(f'{BK}/{os.path.basename(f)}'):shutil.copy(f,BK)
    mj=json.load(open(f))
    for k,v in mj.items():
        if any(f'_tex{ti}.png|' in k for ti in tis):v.update(metallic=1.0,smoothness=0.0)
    json.dump(mj,open(f,'w'),indent=1)
