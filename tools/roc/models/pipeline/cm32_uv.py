"""CM-32 (Shawn 27 Nov 02:2x: "The current CM-32 textures look really cartoony. Please port the CM-34 textures' level of detail"): the seller's
CM-32 paints its camo with flat-colour materials (Color_A..D, no textures), so there is nothing to put detail on. This gives every painted face
one new material 'hull' with its own non-overlapping UVs (Smart UV Project across all painted parts) and a placeholder 2048 texture; camo3d.py
and weather_fam.py then paint it. Glass, lights, tyres, guns and steel parts keep their materials. usage: blender -b -P cm32_uv.py -- IN.glb OUT.glb"""
import bpy,sys,re,math
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
PAINT=re.compile(r'^(Color_[ABCD]_blinn\d|lambert1|blinn3|Interior_Color_blinn2)')   # v3: the near-white 'interior' parts (roof hatches, vision-block frames) are outside too
img=bpy.data.images.new('cm32_hull_BaseColor',2048,2048);img.pixels=[0.5,0.5,0.5,1.0]*(2048*2048);img.filepath_raw='/tmp/cm32_hull_BaseColor.png';img.file_format='PNG';img.save();img.pack()
hull=bpy.data.materials.new('hull');hull.use_nodes=True;nt=hull.node_tree;b=nt.nodes['Principled BSDF'];t=nt.nodes.new('ShaderNodeTexImage');t.image=img;nt.links.new(t.outputs[0],b.inputs['Base Color']);b.inputs['Roughness'].default_value=0.6;b.inputs['Metallic'].default_value=0.0
for m in bpy.data.materials:
    if m.name.startswith('Tire_Color'):m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.03,0.03,0.03,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.9   # v3: rubber, not mid-grey 0.154
objs=[]
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    ids=[i for i,m in enumerate(o.data.materials) if m and PAINT.search(m.name)]
    if not ids:continue
    o.data.materials.append(hull);hi=len(o.data.materials)-1
    for p in o.data.polygons:
        p.select=p.material_index in ids
        if p.select:p.material_index=hi
    if not o.data.uv_layers:o.data.uv_layers.new()
    objs.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.003,area_weight=0.0,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
n=sum(1 for o in objs for p in o.data.polygons if o.data.materials[p.material_index]==hull)
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB');print('CM32UV painted faces',n,'objects',len(objs))
