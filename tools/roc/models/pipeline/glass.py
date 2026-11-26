"""Mark glass materials (glass/window/canopy/boli) of a converted model as clear glass, as build_jp.py does. usage: glass.py SLUG"""
import json,re,sys,os
from pygltflib import GLTF2
s=sys.argv[1];D=os.path.dirname(os.path.abspath(__file__))+'/../veh'
g=GLTF2().load(f'{D}/x/{s}/{s}.glb');glass=[i for i,m in enumerate(g.materials) if re.search(r'(?i)glass|window|canopy|boli|gls|cpt|玻璃|^hud$',m.name or '') and not re.search(r'(?i)(red|blu|grn|green)gl',m.name or '')]   # 26 Nov: Chinese name, HUD; nav lights stay coloured
cols={i:','.join(f'{x:.4f}' for x in (g.materials[i].pbrMetallicRoughness.baseColorFactor or [1,1,1,1])) for i in glass}   # untextured materials are keyed by colour
for name in (f'm_roc_{s}_static',f'm_roc_{s}_lo_static'):
    p=f'{D}/models/{name}.mat.json';mj=json.load(open(p))
    for k in mj:
        if any(k.startswith(f'{name}_tex{i}.png|') for i in glass) or (k.startswith('|') and k[1:] in cols.values()):mj[k].update(clearGlass=True,opacity=0.1,alpha='BLEND',metallic=0.0,smoothness=0.95)
    json.dump(mj,open(p,'w'),indent=1)
print(s,'glass',[g.materials[i].name for i in glass])
