import bpy,sys,mathutils as mu
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
for o in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
    ps=[o.matrix_world@mu.Vector(c) for c in o.bound_box];mn=[round(min(p[i] for p in ps),1) for i in range(3)];mx=[round(max(p[i] for p in ps),1) for i in range(3)]
    print('BB',o.name,mn,mx)
