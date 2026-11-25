"""Mark glass materials (glass/window/canopy/boli) of a converted model as clear glass, as build_jp.py does. usage: glass.py SLUG"""
import json,re,sys,os
from pygltflib import GLTF2
s=sys.argv[1];D=os.path.dirname(os.path.abspath(__file__))+'/../veh'
g=GLTF2().load(f'{D}/x/{s}/{s}.glb');glass=[i for i,m in enumerate(g.materials) if re.search(r'(?i)glass|window|canopy|boli|gls|cpt',m.name or '')]
for name in (f'm_roc_{s}_static',f'm_roc_{s}_lo_static'):
    p=f'{D}/models/{name}.mat.json';mj=json.load(open(p))
    for k in mj:
        if any(k.startswith(f'{name}_tex{i}.png|') for i in glass):mj[k].update(clearGlass=True,opacity=0.1,alpha='BLEND',metallic=0.0,smoothness=0.95)
    json.dump(mj,open(p,'w'),indent=1)
print(s,'glass',[g.materials[i].name for i in glass])
