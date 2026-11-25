import bpy,sys,json,numpy as np
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125/inf/tools');import lm_auto
KEY,cfgp=sys.argv[sys.argv.index('--')+1:];C=json.load(open(cfgp))[KEY]
bpy.ops.wm.read_factory_settings(use_empty=True)
if C['source']=='GLB':bpy.ops.import_scene.gltf(filepath='/home/sam/tars/work/ba-dev/replicas/codex/work/rigging-prep/out/BA_US_Ranger_Rifle1.glb',bone_heuristic='TEMPERANCE')
else:bpy.ops.import_scene.fbx(filepath=C['source'])
import math
from mathutils import Euler
BR=Euler([math.radians(x) for x in C.get('bonerot',[0,0,0])]).to_matrix().to_4x4()
sa=next(o for o in bpy.data.objects if o.type=='ARMATURE');B={k:np.array(BR@sa.matrix_world@sa.data.bones[v].head_local) for k,v in C['bones'].items()}
V=np.concatenate([np.array([bpy.data.objects[n].matrix_world@v.co for v in bpy.data.objects[n].data.vertices]) for n in C['meshes']])
E=lm_auto.estimate(V)
for k in sorted(B):print('ERR',KEY,k,'est',np.round(E[k],3),'true',np.round(B[k],3),'cm',round(100*np.linalg.norm(E[k]-B[k]),1))
for s in 'lr':
    for f in ('index','ring','thumb'):
        a=np.array(E[f+'_01_'+s])-E['hand_'+s];b=B[f+'_01_'+s]-B['hand_'+s];print('ANG',KEY,f,s,round(float(np.degrees(np.arccos(a@b/np.linalg.norm(a)/np.linalg.norm(b)))),1))
    for p,q in (('upperarm','lowerarm'),('lowerarm','hand')):
        a=np.array(E[q+'_'+s])-E[p+'_'+s];b=B[q+'_'+s]-B[p+'_'+s];print('SEG',KEY,p,s,'angle',round(float(np.degrees(np.arccos(a@b/np.linalg.norm(a)/np.linalg.norm(b)))),1),'len est/true',round(np.linalg.norm(a)/np.linalg.norm(b),2))
