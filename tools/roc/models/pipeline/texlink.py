# Link colour + normal maps to a GLB's materials by name: TX_<material>_(BaseColor|Diffuse).png and TX_<material>_Normal.png. usage: -- IN.glb OUT.glb TEXDIR
import bpy,sys,os,glob
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
for o in [o for o in bpy.data.objects if o.type=='MESH' and any(m and m.name.startswith('Ground') for m in o.data.materials)]:bpy.data.objects.remove(o,do_unlink=True);print('DROP ground')
F={os.path.basename(f).lower():f for f in glob.glob(a[2]+'/**/*.png',recursive=True)}
def find(m,kinds):
    for k in kinds:
        for n in (f'tx_{m}_{k}.png',f'{m}_{k}.png'):
            if n.lower() in F:return F[n.lower()]
for m in bpy.data.materials:
    key=m.name.split('.')[0].replace('mat_','');bc=find(key,('BaseColor','Diffuse'))
    if not bc or not m.node_tree:print('NOTEX',m.name);continue
    nt=m.node_tree;b=next(x for x in nt.nodes if x.type=='BSDF_PRINCIPLED')
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(bc);nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    nr=find(key,('Normal',))
    if nr:
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=bpy.data.images.load(nr);tn.image.colorspace_settings.name='Non-Color';nm=nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    print('TEX',m.name,os.path.basename(bc))
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB')
