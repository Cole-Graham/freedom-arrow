"""Render a lit card portrait from the corrected model and installed PBR maps.

Runs in Blender; writes an image only. It does not export or alter game geometry.
"""
import argparse,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('model_dir',type=Path);p.add_argument('maps_dir',type=Path);p.add_argument('output',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(a.model_dir/'black-eagle-corrected.blend'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in list(bpy.data.objects):
 if o.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)
def material(stem):
 m=bpy.data.materials.new('Portrait '+stem);m.use_nodes=True;n=m.node_tree;n.nodes.clear();out=n.nodes.new('ShaderNodeOutputMaterial');b=n.nodes.new('ShaderNodeBsdfPrincipled');n.links.new(b.outputs['BSDF'],out.inputs['Surface'])
 def texture(suffix,linear=False):
  im=bpy.data.images.load(str(a.maps_dir/(stem+suffix)),check_existing=False)
  if linear:im.colorspace_settings.name='Non-Color'
  node=n.nodes.new('ShaderNodeTexImage');node.image=im;return node
 col=texture('.png');n.links.new(col.outputs['Color'],b.inputs['Base Color'])
 mask=texture('_mask.png',True);channels=n.nodes.new('ShaderNodeSeparateColor');n.links.new(mask.outputs['Color'],channels.inputs[0]);n.links.new(channels.outputs['Red'],b.inputs['Metallic'])
 inv=n.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;n.links.new(mask.outputs['Alpha'],inv.inputs[1]);n.links.new(inv.outputs[0],b.inputs['Roughness'])
 normal=texture('_n.png',True);nm=n.nodes.new('ShaderNodeNormalMap');n.links.new(normal.outputs['Color'],nm.inputs['Color']);n.links.new(nm.outputs['Normal'],b.inputs['Normal'])
 return m
body=material('m_blackeagle_cg_tex0');tracks=material('m_blackeagle_cg_tex1')
for o in meshes:
 o.data.materials.clear();o.data.materials.append(tracks if 'Track' in o.name else body)
 for face in o.data.polygons:face.material_index=0
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_x=768;s.render.resolution_y=512;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.view_settings.exposure=0.6;s.view_settings.gamma=1
s.world=bpy.data.worlds.new('Bright portrait studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.5,.5,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
def look(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((3,-6,9),2200,7),((-6,-2,5),1500,7),((2,6,7),1800,6)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;look(o,(0,0,1))
bpy.context.view_layer.update();points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)]);target=(lo+hi)*.5
bpy.ops.object.camera_add(location=target+Vector((10,-14,11)));cam=bpy.context.object;look(cam,target);cam.data.type='ORTHO';s.camera=cam;bpy.context.view_layer.update();inv=cam.matrix_world.inverted();view=[inv@v for v in points];width=max(v.x for v in view)-min(v.x for v in view);height=max(v.y for v in view)-min(v.y for v in view);cam.data.ortho_scale=max(width,height*1.5)/.90
s.render.filepath=str(a.output);bpy.ops.render.render(write_still=True)
print('PORTRAIT_RENDERED',a.output)
