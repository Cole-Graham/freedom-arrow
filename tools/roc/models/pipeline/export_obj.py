# Open a .blend, keep one object, export it as FBX in metres. usage: blender -b IN.blend -P export_obj.py -- OBJECT OUT.fbx
import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
for o in list(bpy.data.objects):
    if o.name!=a[0]:bpy.data.objects.remove(o)
o=bpy.data.objects[a[0]];print('EXP',o.name,o.dimensions[:],o.rotation_euler[:],o.scale[:])
bpy.ops.export_scene.fbx(filepath=a[1],use_selection=False,apply_unit_scale=True,global_scale=1.0)
