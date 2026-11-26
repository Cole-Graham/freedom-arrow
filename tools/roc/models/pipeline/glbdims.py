import bpy,sys,mathutils as mu
for f in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
    ps=[o.matrix_world@mu.Vector(c) for o in bpy.data.objects if o.type=='MESH' for c in o.bound_box]
    print('DIMS',f.split('/')[-1],[round(max(p[i] for p in ps)-min(p[i] for p in ps),5) for i in range(3)],'objs',len([o for o in bpy.data.objects if o.type=='MESH']))
