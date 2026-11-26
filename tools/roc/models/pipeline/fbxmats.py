import bpy,sys,mathutils as mu
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=f)
for o in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
    ps=[o.matrix_world@mu.Vector(c) for c in o.bound_box];d=[round(max(p[i] for p in ps)-min(p[i] for p in ps),2) for i in range(3)]
    ms=[]
    for m in o.data.materials:
        if not m:continue
        im=[n.image.name+('('+n.image.filepath.split('/')[-1].split('\\')[-1]+')') for n in (m.node_tree.nodes if m.use_nodes else []) if n.type=='TEX_IMAGE' and n.image]
        ms.append(m.name+':'+','.join(im))
    print('OB',o.name,sum(len(p.vertices)-2 for p in o.data.polygons),d,ms)
