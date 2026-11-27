"""EC225: the seller's window parts (objects named *glass*) share the body material and get their see-through from its alpha map. Move them to their
own untextured 'canopy_glass' material (canopy_split.py colour, so tint_glass.py can tint it) and make the body opaque.
usage: blender -b -P ec225_glass.py -- IN.glb OUT.glb"""
import bpy,sys,re
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
g=bpy.data.materials.new('canopy_glass');g.use_nodes=True;b=g.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(0.85,0.9,0.95,1);b.inputs['Alpha'].default_value=0.15
n=0
for o in [o for o in bpy.data.objects if o.type=='MESH' and re.search(r'(?i)glass',o.name) and not re.search(r'(?i)landinglights',o.name)]:
    o.data.materials.clear();o.data.materials.append(g);n+=1
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB');print('GLASS objects',n)
