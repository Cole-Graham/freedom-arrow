"""MTWV (Shawn 28 Nov 03:4x): Navistar 7400 cab + chassis (his Drive model) + the vanilla MTV cargo bed and canvas, fitted to the frame
behind the cab like his reference photo. Blender, background: blender -b "Navistar 7400.blend" -P mtwv_build.py -- OUT.glb
- Navistar parts get PBR materials from its UE maps (BaseColor recoloured by recolour.py; Normal; ORM: G roughness, B metal).
- MTV bed: vanilla US_MTV BASE_MESH faces above the frame (centroid y >= 1.25 m) behind the cab (z <= 0.85 m) + the whole TENT, from the
  vanilla export (Unity space), with the MTV sheet (olive). Stretched to the Navistar frame: length x1.09 (4.78 -> 5.21 m), width x1.0,
  its underside (y 1.25) on the Navistar frame top (z 0.98).
- Decimated to an Arsenal budget, front turned to Blender -Y (glTF +Z, the game front)."""
import bpy,sys,os,math,numpy as np,bmesh
out=sys.argv[sys.argv.index('--')+1]
H=os.path.dirname(os.path.abspath(__file__));T=H+'/../../../dl12/files/Textures_UE';RT=H+'/tex'
E='/home/sam/tars/work/ba-dev/replicas/codex/work/vanilla-export-20261123/out/US_MTV/mesh/'
def img(p):
    return bpy.data.images.load(p,check_existing=True)
def pbr(name,base,nrm=None,orm=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=img(base);nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    if nrm:
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=img(nrm);tn.image.colorspace_settings.name='Non-Color'
        nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    if orm:
        to=nt.nodes.new('ShaderNodeTexImage');to.image=img(orm);to.image.colorspace_settings.name='Non-Color'
        sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(to.outputs['Color'],sp.inputs['Color'])
        nt.links.new(sp.outputs['Green'],b.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],b.inputs['Metallic'])
    else: b.inputs['Roughness'].default_value=0.7;b.inputs['Metallic'].default_value=0.0
    return m
MAP={'NI_Cabin':'Cabin','NI_Frame':'Frame','NI_Equipment':'Equipment','NI_Interior':'Interior'}
mats={}
def ni(key):
    if key not in mats:
        base=f'{RT}/NI_{key}_BaseColor.png' if os.path.exists(f'{RT}/NI_{key}_BaseColor.png') else f'{T}/NI_{key}_BaseColor.jpg'
        mats[key]=pbr('MTWV_'+key,base,f'{T}/NI_{key}_Normal.jpg',f'{T}/NI_{key}_OcclusionRoughnessMetallic.jpg')
    return mats[key]
glass=bpy.data.materials.new('MTWV_Glass');glass.use_nodes=True;glass.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.10,0.12,0.13,0.82)
DEC={'NI_Frame':0.22,'NI_Interior':0.12,'NI_Equipment':0.25,'NI_Cabin':0.75,'NI_B_Wheel':0.3,'NI_F_Wheel':0.45,'NI_Glass':1.0}
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    key=next((k for k in MAP if o.name.startswith(k)),None)
    o.data.materials.clear()
    if o.name.startswith('NI_Glass'):o.data.materials.append(glass)
    elif 'Wheel' in o.name:o.data.materials.append(ni('Wheel'))
    else:o.data.materials.append(ni(MAP[key]))
    r=next((v for k,v in DEC.items() if o.name.startswith(k)),1.0)
    if r<1.0:
        bpy.context.view_layer.objects.active=o;md=o.modifiers.new('dec','DECIMATE');md.ratio=r
        with bpy.context.temp_override(object=o):bpy.ops.object.modifier_apply(modifier='dec')
# MTV bed + canvas
def mtv(npzname,keep):
    z=np.load(E+npzname);v,f,uv=z['v'],z['f0'],z['uv'];c=v[f].mean(1);f=f[keep(c)]
    used=np.unique(f);remap=-np.ones(len(v),int);remap[used]=np.arange(len(used));vv=v[used];ff=remap[f]
    P=np.c_[-(vv[:,2]-0.85)*1.09-2.93, vv[:,0]*1.0, vv[:,1]-1.25+0.98]
    me=bpy.data.meshes.new(npzname);me.from_pydata(P.tolist(),[],ff.tolist());me.update()
    ul=me.uv_layers.new(name='UVMap');lu=uv[used]
    for poly in me.polygons:
        for li in poly.loop_indices:ul.data[li].uv=lu[me.loops[li].vertex_index]
    ob=bpy.data.objects.new('MTV_'+npzname.split('_')[0],me);bpy.context.scene.collection.objects.link(ob);return ob
bedm=pbr('MTWV_Bed',RT+'/MTV_Bed_BaseColor.png')
for o in (mtv('BASE_MESH_8523.npz',lambda c:(c[:,1]>=1.25)&(c[:,2]<=0.85)),mtv('TENT_34027.npz',lambda c:np.ones(len(c),bool))):
    o.data.materials.append(bedm);print('MTV part',o.name,len(o.data.polygons))
for o in bpy.data.objects:
    if o.type=='MESH' and o.parent is None: o.matrix_world=__import__('mathutils').Matrix.Rotation(math.radians(90),4,'Z')@o.matrix_world
ms=[o for o in bpy.data.objects if o.type=='MESH']
print('TRIS',{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in ms},'total',sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in ms))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=True,export_apply=True)
print('WROTE',out)
