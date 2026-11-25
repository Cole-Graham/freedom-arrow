# Remove mesh objects lying wholly above a height (display props). usage: blender -b -P dropabove.py -- IN.glb OUT.glb MINZ
import bpy,sys,mathutils as mu
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0]);n=0
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    if min((o.matrix_world@mu.Vector(c)).z for c in o.bound_box)>float(a[2]):bpy.data.objects.remove(o,do_unlink=True);n+=1
print('DROPPED',n);bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB')
