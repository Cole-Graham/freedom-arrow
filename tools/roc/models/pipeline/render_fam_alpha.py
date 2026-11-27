"""(ROC copy with ALPHA=1 support) Render a .fam as the game sees it (Unity space: +Y up, +Z front, X mirrored) from the front-left, with its textures and masks."""
import bpy,sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
a=sys.argv[sys.argv.index('--')+1:];fam,out=a[0],a[1];d=os.path.dirname(fam)
bpy.ops.wm.read_factory_settings(use_empty=True)
mats={};allp=[]
import json as _j
_mj=os.path.join(d,os.path.basename(fam)[:-4]+'.mat.json');MJ=_j.load(open(_mj)) if os.path.exists(_mj) else {}   # ROC copy: show clearGlass as FAModels does (neutral, colour ignored)
for bone,subs in read_fam(fam):
    for k,sb in enumerate(subs):
        n=len(sb['pos'])//3
        # Unity (x,y,z) -> Blender (x, z, y) with z front: put Unity +Z as Blender -Y so the front faces the camera at -Y
        V=[(-sb['pos'][3*i],-sb['pos'][3*i+2],sb['pos'][3*i+1]) for i in range(n)];allp+=V
        F=[tuple(sb['idx'][j:j+3]) for j in range(0,len(sb['idx']),3)]
        me=bpy.data.meshes.new(f'{bone}{k}');me.from_pydata(V,[],F);uvl=me.uv_layers.new()
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi=me.loops[li].vertex_index;uvl.data[li].uv=(sb['uv'][2*vi],1+sb['uv'][2*vi+1])
        t=sb['tex'];kk=(t,tuple(round(x,4) for x in sb['col'])) if not t else t
        _key=(t or '')+'|'+','.join(f'{x:.4f}' for x in sb['col']);_g=MJ.get(_key,{}).get('clearGlass') or MJ.get(_key,{}).get('cockpitDonor')   # 26 Nov: donor glass shown as a light grey tint (US_F16_Glass is grey 0.35, no colour map)
        if _g:kk=('__glass__',)
        if _g and kk not in mats:
            m=bpy.data.materials.new('clearGlass');m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(1,1,1,1);b.inputs['Roughness'].default_value=0.05;b.inputs['Alpha'].default_value=max(0.12,MJ[_key].get('opacity',0.1))
            if MJ[_key].get('cockpitDonor'):b.inputs['Base Color'].default_value=(0.35,0.35,0.35,1);b.inputs['Alpha'].default_value=0.3
            mats[kk]=m
        if kk not in mats:
            m=bpy.data.materials.new(t);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
            if t and os.path.exists(os.path.join(d,t)):
                tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(os.path.join(d,t));nt.links.new(tx.outputs[0],b.inputs['Base Color'])
                if any(abs(x-1)>1e-3 for x in sb['col'][:3]):mx=nt.nodes.new('ShaderNodeMix');mx.data_type='RGBA';mx.blend_type='MULTIPLY';mx.inputs['Factor'].default_value=1;nt.links.new(tx.outputs[0],mx.inputs['A']);mx.inputs['B'].default_value=tuple(sb['col'][:3])+(1,);nt.links.new(mx.outputs['Result'],b.inputs['Base Color'])   # 27 Nov: FAModels multiplies the map by the colour (_BaseColor)
                if os.environ.get('ALPHA'):nt.links.new(tx.outputs['Alpha'],b.inputs['Alpha'])   # ROC copy: show alpha cut-outs (wire grilles)
                mk=os.path.join(d,t[:-4]+'_mask.png')
                if os.path.exists(mk):
                    km=nt.nodes.new('ShaderNodeTexImage');km.image=bpy.data.images.load(mk);km.image.colorspace_settings.name='Non-Color';sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(km.outputs[0],sp.inputs[0]);nt.links.new(sp.outputs[0],b.inputs['Metallic'])
                    P=MJ.get(_key,{});mr=P.get('metallicRemap',[0,1]);sr=P.get('smoothnessRemap',[0,1])   # 26 Nov: FAModels metallic/smoothness remaps
                    rm=nt.nodes.new('ShaderNodeMapRange');rm.inputs[3].default_value,rm.inputs[4].default_value=mr;nt.links.new(sp.outputs[0],rm.inputs[0]);nt.links.new(rm.outputs[0],b.inputs['Metallic'])
                    rs=nt.nodes.new('ShaderNodeMapRange');rs.inputs[3].default_value,rs.inputs[4].default_value=1-sr[0],1-sr[1];nt.links.new(km.outputs['Alpha'],rs.inputs[0]);nt.links.new(rs.outputs[0],b.inputs['Roughness'])
                elif _key in MJ:b.inputs['Metallic'].default_value=MJ[_key].get('metallic',0.1);b.inputs['Roughness'].default_value=1-MJ[_key].get('smoothness',0.3)
            else:
                b.inputs['Base Color'].default_value=tuple(sb['col'])
                if _key in MJ:b.inputs['Metallic'].default_value=MJ[_key].get('metallic',0.1);b.inputs['Roughness'].default_value=1-MJ[_key].get('smoothness',0.3)
            mats[kk]=m
        me.materials.append(mats[kk]);o=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(o)
xs=[p[0] for p in allp];ys=[p[1] for p in allp];zs=[p[2] for p in allp];c=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2);size=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.render.resolution_x=960;sc.render.resolution_y=600
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.62,0.7,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.8
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(50),0,math.radians(-30)));bpy.context.object.data.energy=3.5
r=size*float(os.environ.get('RS','1.25'));t=math.radians(float(os.environ.get('AZ','-120')))   # camera at front-left (front is -Y)
bpy.ops.object.camera_add(location=(c[0]+r*math.cos(t),c[1]+r*math.sin(t),c[2]+size*0.35));cam=bpy.context.object;sc.camera=cam
k=cam.constraints.new('TRACK_TO');bpy.ops.object.empty_add(location=c);k.target=bpy.context.object;k.track_axis='TRACK_NEGATIVE_Z';k.up_axis='UP_Y'
sc.render.filepath=os.path.abspath(out);bpy.ops.render.render(write_still=True)
print('dims',round(max(xs)-min(xs),2),round(max(ys)-min(ys),2),round(max(zs)-min(zs),2))
