"""canopy_split.py IN.glb OUT.glb MATERIAL OPACITY.png [OBJECT_REGEX]: faces of MATERIAL whose UV centre is see-through in OPACITY.png (< 0.5) move to a new
untextured 'canopy_glass' material, so glass.py can make them clear glass (F-CK-1, 26 Nov: the canopy shared the cockpit texture and was only
cut out, Shawn: "make sure the glass of the canopy is in correct color ... like glass")."""
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
img=bpy.data.images.load(a[3]);w,h=img.size;px=np.empty(w*h*4,np.float32);img.pixels.foreach_get(px);op=px.reshape(h,w,4)[...,0]
g=bpy.data.materials.new('canopy_glass');g.use_nodes=True;b=g.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(0.85,0.9,0.95,1);b.inputs['Alpha'].default_value=0.15
g.surface_render_method='BLENDED' if hasattr(g,'surface_render_method') else None
import re
OBJ=a[4] if len(a)>4 else '.'
g=bpy.data.materials.get('canopy_glass_') or g
moved=0
for o in [o for o in bpy.data.objects if o.type=='MESH' and re.search(OBJ,o.name)]:
    me=o.data;ids=[i for i,m in enumerate(me.materials) if m and m.name.split('.')[0]==a[2]]
    if not ids:continue
    me.materials.append(g);gi=len(me.materials)-1;uv=me.uv_layers.active.data;cs=[]
    for p in me.polygons:
        if p.material_index not in ids:continue
        u=np.mean([uv[l].uv[0] for l in p.loop_indices]);v=np.mean([uv[l].uv[1] for l in p.loop_indices])
        x=int((u%1)*w)%w;y=int((v%1)*h)%h
        if op[y,x]<0.5:p.material_index=gi;moved+=1;cs.append(tuple(o.matrix_world@p.center))
    C=np.array(cs) if cs else None
    if C is not None:print('OBJ',o.name,len(cs),'faces, box',C.min(0).round(2).tolist(),C.max(0).round(2).tolist())
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB')
print('CANOPY moved',moved,'faces')
