import bpy,json,sys,numpy as np
from pathlib import Path
from math import radians
old,new,out=sys.argv[sys.argv.index('--')+1:];rows=[]
for label,root in [('before',old),('after',new)]:
 for key in ['regular_woodland','sf_condor_desert']:
  bpy.ops.wm.open_mainfile(filepath=str(Path(root)/key/'rig.blend'))
  arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');obj=next(o for o in bpy.data.objects if o.type=='MESH' and o.name==key+'_lod0')
  for side,sign in [('Left',1),('Right',-1)]:
   for name,angle in [('ForeArm',65),('Hand',25)]:
    b=arm.pose.bones[side+name];b.rotation_mode='XYZ';b.rotation_euler.y=radians(angle*sign)
  bpy.context.view_layer.update();evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
  for bone in ['LeftForeArm','RightForeArm','LeftHand','RightHand']:
   group=obj.vertex_groups[bone].index;selected=[v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group==group)>.6];p=np.array([list(mesh.vertices[i].co) for i in selected]);eig=np.linalg.eigvalsh(np.cov(p.T));rows.append({'fit':label,'model':key,'region':bone,'vertices':len(p),'pca_std_m':np.sqrt(np.maximum(eig,0)).tolist()})
  evaluated.to_mesh_clear()
Path(out).write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
