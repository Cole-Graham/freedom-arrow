import bpy,sys,json
from pathlib import Path
from math import radians
from mathutils import Vector
old,new,out=sys.argv[sys.argv.index('--')+1:];out=Path(out).resolve();out.mkdir(exist_ok=True)
for label,root in [('before',old),('trial',new)]:
 for key in ['regular_woodland','sf_condor_desert']:
  bpy.ops.wm.open_mainfile(filepath=str(Path(root)/key/'rig.blend'))
  arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
  for side,sign in [('Left',1),('Right',-1)]:
   for name,angle in [('ForeArm',65),('Hand',25)]:
    b=arm.pose.bones[side+name];b.rotation_mode='XYZ';b.rotation_euler.y=radians(angle*sign)
  bpy.context.view_layer.update()
  s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100
  cam=bpy.data.objects.new('Audit camera',bpy.data.cameras.new('Audit camera'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.45;cam.location=(2.2,-5,1.4);cam.rotation_euler=(Vector((0,0,1.24))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'{key}-{label}-bent.png');bpy.ops.render.render(write_still=True)
