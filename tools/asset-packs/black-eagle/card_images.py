import bpy,sys
from pathlib import Path
from mathutils import Vector
r=Path(sys.argv[sys.argv.index('--')+1]).absolute()
bpy.ops.wm.open_mainfile(filepath=str(r/'black-eagle.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Card studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.4,.4,1)
def look(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for pos in [(3,-4,8),(-4,3,7)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=2200;o.data.size=7;look(o,(0,0,1))
bpy.ops.object.camera_add(location=(10,-13,9));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12;s.camera=cam;look(cam,(0,-1,1));s.render.resolution_x=768;s.render.resolution_y=512;s.render.filepath=str(r/'portrait.png');bpy.ops.render.render(write_still=True)
white=bpy.data.materials.new('White silhouette');white.use_nodes=True;n=white.node_tree;n.nodes.clear();out=n.nodes.new('ShaderNodeOutputMaterial');em=n.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1);n.links.new(em.outputs[0],out.inputs[0])
for o in bpy.data.objects:
 if o.type=='MESH':
  o.data.materials.clear();o.data.materials.append(white)
  for p in o.data.polygons:p.material_index=0
cam.location=(-15,0,1.6);look(cam,(0,-1,1.3));cam.data.ortho_scale=11.2;s.render.resolution_x=768;s.render.resolution_y=256;s.render.filepath=str(r/'silhouette.png');bpy.ops.render.render(write_still=True)
