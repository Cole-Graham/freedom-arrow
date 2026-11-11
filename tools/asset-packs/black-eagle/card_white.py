import bpy,sys,math
from pathlib import Path
from mathutils import Vector
r=Path(sys.argv[sys.argv.index('--')+1]).absolute()
bpy.ops.wm.open_mainfile(filepath=str(r/'black-eagle-corrected.blend'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
# Icon-only shortening: no source .fam or game geometry is changed.
gun=next(o for o in meshes if o.name=='MainGun');inv=gun.matrix_world.inverted();rear=max((gun.matrix_world@v.co).y for v in gun.data.vertices)
for v in gun.data.vertices:
 w=gun.matrix_world@v.co;w.y=rear+(w.y-rear)*.70;v.co=inv@w
white=bpy.data.materials.new('White card');white.use_nodes=True;nt=white.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1);nt.links.new(em.outputs[0],out.inputs[0])
for o in meshes:
 o.data.materials.clear();o.data.materials.append(white)
 for p in o.data.polygons:p.material_index=0
bpy.context.view_layer.update();points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_x=512;s.render.resolution_y=256;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
width=(hi.y-lo.y)/.96;centerZ=lo.z+(128-8)/256*(width/2);centerY=(lo.y+hi.y)/2
bpy.ops.object.camera_add(location=(-20,centerY,centerZ));cam=bpy.context.object;cam.rotation_euler=(Vector((0,centerY,centerZ))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=width;s.camera=cam;s.render.filepath=str(r/'card-white-lower.png');bpy.ops.render.render(write_still=True)
