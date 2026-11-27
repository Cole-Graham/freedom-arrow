# BA Codex 26 Nov (EDGE=1: R = edge wear 1 - dot(bevel normal 2 cm, normal) x 4, for worn metal) bake per-material geometry maps for the HF-IIE weathering: R = height (z / 3 m), G = up-facing (normal z * 0.5 + 0.5), B = pointiness (edges).
import bpy,sys,os
a=sys.argv[sys.argv.index('--')+1:];glb,out=a[0],a[1];os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','4'));sc.render.bake.margin=8
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices();[setattr(d,'use',True) for d in pr.devices];sc.cycles.device='GPU'
except Exception as e:print('GPU off',e)
ims={}
for m in bpy.data.materials:
    if not m.use_nodes:continue
    nt=m.node_tree;[nt.nodes.remove(n) for n in list(nt.nodes)]
    o=nt.nodes.new('ShaderNodeOutputMaterial');e=nt.nodes.new('ShaderNodeEmission');g=nt.nodes.new('ShaderNodeNewGeometry');sp=nt.nodes.new('ShaderNodeSeparateXYZ');sn=nt.nodes.new('ShaderNodeSeparateXYZ')
    dz=nt.nodes.new('ShaderNodeMath');dz.operation='DIVIDE';dz.inputs[1].default_value=3.0
    nz=nt.nodes.new('ShaderNodeMath');nz.operation='MULTIPLY_ADD';nz.inputs[1].default_value=0.5;nz.inputs[2].default_value=0.5
    cc=nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(g.outputs['Position'],sp.inputs[0]);nt.links.new(sp.outputs['Z'],dz.inputs[0]);nt.links.new(dz.outputs[0],cc.inputs[0])
    nt.links.new(g.outputs['Normal'],sn.inputs[0]);nt.links.new(sn.outputs['Z'],nz.inputs[0]);nt.links.new(nz.outputs[0],cc.inputs[1])
    nt.links.new(g.outputs['Pointiness'],cc.inputs[2]);nt.links.new(cc.outputs[0],e.inputs[0]);nt.links.new(e.outputs[0],o.inputs[0])
    if os.environ.get('EDGE'):
        bv=nt.nodes.new('ShaderNodeBevel');bv.samples=16;bv.inputs['Radius'].default_value=0.02;dp=nt.nodes.new('ShaderNodeVectorMath');dp.operation='DOT_PRODUCT'
        nt.links.new(bv.outputs[0],dp.inputs[0]);nt.links.new(g.outputs['Normal'],dp.inputs[1]);iv=nt.nodes.new('ShaderNodeMath');iv.operation='MULTIPLY_ADD';iv.inputs[1].default_value=-4;iv.inputs[2].default_value=4
        nt.links.new(dp.outputs['Value'],iv.inputs[0]);nt.links.new(iv.outputs[0],e.inputs[0])
    im=bpy.data.images.new('geo_'+m.name,2048,2048,float_buffer=True);im.colorspace_settings.name='Non-Color'
    t=nt.nodes.new('ShaderNodeTexImage');t.image=im;nt.nodes.active=t;ims[m.name]=im
for ob in bpy.data.objects:ob.select_set(ob.type=='MESH')
bpy.context.view_layer.objects.active=[o for o in bpy.data.objects if o.type=='MESH'][0]
bpy.ops.object.bake(type='EMIT')
for n,im in ims.items():
    im.filepath_raw=f"{out}/{'edge' if os.environ.get('EDGE') else 'geo'}_{n}.exr";im.file_format='OPEN_EXR';im.save();print('BAKED',n)
