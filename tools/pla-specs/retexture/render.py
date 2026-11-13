import bpy,sys,os,math
argv=sys.argv[sys.argv.index('--')+1:];texdir,out,cam_az=argv[0],argv[1],float(argv[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=os.path.abspath('zsl92.obj'),forward_axis='NEGATIVE_Z',up_axis='Y')
def mat(name):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
    o=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(b.outputs[0],o.inputs[0])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(texdir,name+'.png'));nt.links.new(t.outputs[0],b.inputs['Base Color'])
    if name.endswith('tex1'):b.inputs['Roughness'].default_value=0.05;b.inputs['Metallic'].default_value=0.0;return m
    mk=os.path.join(texdir,name+'_mask.png')
    if os.path.exists(mk):
        k=nt.nodes.new('ShaderNodeTexImage');k.image=bpy.data.images.load(mk);k.image.colorspace_settings.name='Non-Color'
        sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(k.outputs[0],sep.inputs[0]);nt.links.new(sep.outputs[0],b.inputs['Metallic'])
        inv=nt.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;nt.links.new(k.outputs['Alpha'],inv.inputs[1]);nt.links.new(inv.outputs[0],b.inputs['Roughness'])
    else:b.inputs['Roughness'].default_value=1-0.18;b.inputs['Metallic'].default_value=0
    nm=os.path.join(texdir,name+'_n.png')
    if os.path.exists(nm):
        n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(nm);n.image.colorspace_settings.name='Non-Color'
        nmn=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(n.outputs[0],nmn.inputs['Color']);nt.links.new(nmn.outputs[0],b.inputs['Normal'])
    return m
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        for i,s in enumerate(o.material_slots):
            nm=s.material.name.split('.')[0];s.material=mat(nm)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.device='CPU';sc.render.resolution_x=1280;sc.render.resolution_y=760
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.55,0.62,0.7,1);bg.inputs[1].default_value=0.9
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(50),0,math.radians(cam_az+40)));bpy.context.object.data.energy=3.5
bpy.ops.mesh.primitive_plane_add(size=40);pl=bpy.context.object;pm=bpy.data.materials.new('g');pm.use_nodes=True;pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.32,0.30,0.26,1);pl.data.materials.append(pm)
r=11;a=math.radians(cam_az);bpy.ops.object.camera_add(location=(r*math.cos(a),r*math.sin(a),4.2));cam=bpy.context.object;sc.camera=cam
c=cam.constraints.new('TRACK_TO');bpy.ops.object.empty_add(location=(0,0,1.0));c.target=bpy.context.object;c.track_axis='TRACK_NEGATIVE_Z';c.up_axis='UP_Y'
cam.data.lens=50;sc.render.filepath=os.path.abspath(out);bpy.ops.render.render(write_still=True)
