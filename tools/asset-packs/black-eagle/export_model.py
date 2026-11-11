"""Convert the supplied assembled OBJ; FBX turret transforms are malformed."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
r=Path(sys.argv[sys.argv.index('--')+1]).absolute()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(r/'source/T95_BlackEagle.obj'),global_scale=.0254,use_split_groups=True)
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert any('Turret' in o.name for o in meshes),[o.name for o in meshes]
def material(name,colour,normal,smooth):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(b.outputs[0],out.inputs[0]);b.inputs['Metallic'].default_value=0
 for filename,kind in [(colour,'colour'),(normal,'normal'),(smooth,'smooth')]:
  im=bpy.data.images.load(str(r/'source/maps'/filename),check_existing=True)
  if kind!='colour':im.colorspace_settings.name='Non-Color'
  n=nt.nodes.new('ShaderNodeTexImage');n.image=im
  if kind=='colour':nt.links.new(n.outputs['Color'],b.inputs['Base Color'])
  elif kind=='normal':
   norm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(n.outputs['Color'],norm.inputs[0]);nt.links.new(norm.outputs[0],b.inputs['Normal'])
  else:
   inv=nt.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;nt.links.new(n.outputs['Color'],inv.inputs[1]);nt.links.new(inv.outputs[0],b.inputs['Roughness'])
 return m
body=material('Black Eagle body','t95_diffuse.tga','T95_normal.tga','smoothiness2.tga')
tracks=material('Black Eagle tracks','track_diffuse.tga','track_normal.tga','track_smoothiness.tga')
for o in meshes:
 o.data.materials.clear();o.data.materials.append(tracks if 'Track' in o.name else body)
 for p in o.data.polygons:p.material_index=0
# Full source geometry is modest (~17k triangles); retain it in both copies.
bpy.ops.export_scene.gltf(filepath=str(r/'black-eagle.glb'),export_format='GLB',export_apply=True,export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(r/'black-eagle.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Black Eagle preview studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1)
def look(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((2,-4,8),1600,7),((-5,1,6),1300,6),((2,6,5),900,5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;look(o,(0,0,1))
bpy.ops.object.camera_add(location=(10,-13,9));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12;s.camera=cam;look(cam,(0,-1,1));s.render.image_settings.file_format='PNG';s.render.filepath=str(r/'model-preview.png');bpy.ops.render.render(write_still=True)
print('EXPORTED',[(o.name,len(o.data.vertices)) for o in meshes])
