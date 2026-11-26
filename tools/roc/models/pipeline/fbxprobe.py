import bpy,sys,mathutils as mu
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=f)
ms=[o for o in bpy.data.objects if o.type=='MESH'];ps=[o.matrix_world@mu.Vector(c) for o in ms for c in o.bound_box]
lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in ms)
mats=sorted({m.name for o in ms for m in o.data.materials if m})
imgs=sorted({n.image.name for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image})
print('PROBE',f.split('/')[-1],'objs',len(ms),'tris',tris,'dims',[round(hi[i]-lo[i],2) for i in range(3)],'lo',[round(x,2) for x in lo])
print('PROBE mats',mats[:20]);print('PROBE imgs',imgs[:20]);print('PROBE names',[o.name for o in ms][:25])
