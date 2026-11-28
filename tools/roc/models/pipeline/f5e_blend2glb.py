"""F-5E (Shawn 27 Nov 19:4x) .blend -> GLB with plain image materials a GLB can carry (the hull's node mix is pre-baked by f5e_composite.py).
The 316k-triangle pilot is decimated to ~6k; missiles and the fuel tank go (FA draws its own stores). usage:
blender -b F-5E_Land.blend -P f5e_blend2glb.py -- OUT.glb TEXDIR [gear|nogear]"""
import bpy,sys,os,re
a=sys.argv[sys.argv.index('--')+1:];out,T,mode=a[0],a[1],(a[2] if len(a)>2 else 'gear')
SRC=os.path.dirname(bpy.data.filepath)
def img(p):return bpy.data.images.load(p,check_existing=True)
def mat(name,tex=None,nrm=None,col=(0.5,0.5,0.5,1),metal=0.0,rough=0.5,alpha=1.0):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;b.inputs['Base Color'].default_value=col;b.inputs['Alpha'].default_value=alpha
    if tex:t=nt.nodes.new('ShaderNodeTexImage');t.image=img(tex);nt.links.new(t.outputs[0],b.inputs['Base Color'])
    if nrm:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=img(nrm);t.image.colorspace_settings.name='Non-Color';nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(t.outputs[0],nm.inputs['Color']);nt.links.new(nm.outputs[0],b.inputs['Normal'])
    if alpha<1:m.blend_method='BLEND' if hasattr(m,'blend_method') else None
    return m
NEW={'F-5EMainBody':mat('f5e_hull',T+'/f5e_hull.png',T+'/f5e_hull_n.png'),'F-5E-Inner':mat('f5e_inner',T+'/f5e_hull.png'),
     'PanelMap':mat('f5e_panel',SRC+'/Panel.png'),'Pilot':mat('f5e_pilot',SRC+'/Panel.png'),'Gage':mat('f5e_gage',SRC+'/Panel.png'),
     'GearMap':mat('f5e_gear',SRC+'/GearMap.jpg'),'missleMap':mat('f5e_missile',SRC+'/missile.png'),'HeadGlass':mat('f5e_head',SRC+'/HeadMonitor.png'),
     'BrightSteel':mat('f5e_steel',col=(0.62,0.62,0.6,1),metal=1.0,rough=0.35),'BlackTire':mat('f5e_tyre',col=(0.03,0.03,0.03,1),rough=0.9),
     'TransparentGreen':mat('f5e_hud',col=(0.3,0.6,0.4,1),alpha=0.3),'glass':mat('canopy_glass',col=(0.85,0.9,0.95,1),alpha=0.15)}
DROP=r'^(AIM-9|OilTank)'
if mode=='nogear':DROP=r'^(AIM-9|OilTank|Gear_Back|F-Leg_|Cylinder|Tube|Middle_Gear|BackGearCover|FrontGearCover|mainHull\.00[12]|mainWing\.00[12])'
for o in list(bpy.data.objects):
    if o.type=='MESH' and re.search(DROP,o.name):bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for i,s in enumerate(o.material_slots):
        if s.material and s.material.name in NEW:s.material=NEW[s.material.name]
    if o.name=='Pilot':
        d=o.modifiers.new('dec','DECIMATE');d.ratio=6000/316402;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',use_selection=False,export_apply=True,export_image_format='AUTO')
print('EXPORTED',out,mode,sum(1 for o in bpy.data.objects if o.type=='MESH'),'meshes')
