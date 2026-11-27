"""Export a ROC Arsenal .fam (the in-game geometry) to FBX with its enhanced textures as PNG files.
usage: blender -b -P export_fam_fbx.py -- MODEL.fam OUTDIR NAME
Colour and normal maps come from models/tex_full/ (2048) when present, else from models/.
A FAModels _mask (R metal, A smoothness) is written as separate Metallic and Roughness PNGs.
Materials without a mask get the constant metallic/roughness from the .mat.json."""
import bpy,sys,os,json,shutil
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from famread import read_fam
fam,out,name=sys.argv[sys.argv.index('--')+1:][:3];d=os.path.dirname(os.path.abspath(fam));full=os.path.join(d,'tex_full')
td=os.path.join(out,'textures');os.makedirs(td,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
mj=os.path.join(d,os.path.basename(fam)[:-4]+'.mat.json');MJ=json.load(open(mj)) if os.path.exists(mj) else {}
def src(f):
    for p in (os.path.join(full,f),os.path.join(d,f)):
        if os.path.exists(p):return p
def put(f,role,tint=None):
    """Copy a texture into textures/ with a readable name; return the loaded image. A colour tint (FAModels multiplies the map by the
    sub-mesh colour) is baked into the copy, because FBX does not carry a colour factor on a textured channel."""
    p=src(f)
    if not p:return None
    tinted=tint is not None and any(abs(x-1)>1e-3 for x in tint[:3])
    dst=os.path.join(td,f'{name}_{f.split("_static_")[-1][:-4].replace("_n","").replace("_mask","")}{"_tinted" if tinted else ""}_{role}.png');shutil.copyfile(p,dst)
    im=bpy.data.images.load(dst);im.colorspace_settings.name='sRGB' if role=='BaseColor' else 'Non-Color'
    if tinted:
        a=np.empty(im.size[0]*im.size[1]*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(-1,4);a[:,:3]*=np.array(tint[:3],np.float32)**(1/2.2)
        im.pixels.foreach_set(a.ravel());im.filepath_raw=dst;im.file_format='PNG';im.save()
    return im
def split_mask(f):
    p=src(f)
    if not p:return None,None
    m=bpy.data.images.load(p);w,h=m.size;a=np.empty(w*h*4,np.float32);m.pixels.foreach_get(a);a=a.reshape(-1,4);ims=[]
    for role,ch in (('Metallic',a[:,0]),('Roughness',1-a[:,3])):
        im=bpy.data.images.new(f'{f}_{role}',w,h);px=np.repeat(ch[:,None],4,1);px[:,3]=1;im.pixels.foreach_set(px.ravel())
        im.filepath_raw=os.path.join(td,f'{name}_{f.split("_static_")[-1][:-9]}_{role}.png');im.file_format='PNG';im.save()
        im=bpy.data.images.load(im.filepath_raw);im.colorspace_settings.name='Non-Color';ims.append(im)
    bpy.data.images.remove(m);return ims
mats={}
def material(t,col,key):
    k=key
    if k in mats:return mats[k]
    P=MJ.get(key,{});m=bpy.data.materials.new(f'{name}_{len(mats)}');m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    if P.get('clearGlass') or P.get('cockpitDonor'):
        m.name=f'{name}_glass';b.inputs['Base Color'].default_value=(0.10,0.12,0.13,1) if P.get('clearGlass') else (0.35,0.35,0.35,1);b.inputs['Roughness'].default_value=0.05;b.inputs['Alpha'].default_value=max(0.3,P.get('opacity',0.3))
    elif t and src(t):
        tx=nt.nodes.new('ShaderNodeTexImage');tx.image=put(t,'BaseColor',col);nt.links.new(tx.outputs[0],b.inputs['Base Color'])
        if P.get('alpha') in ('MASK','BLEND'):nt.links.new(tx.outputs['Alpha'],b.inputs['Alpha'])
        n=put(t[:-4]+'_n.png','Normal')
        if n:
            tn=nt.nodes.new('ShaderNodeTexImage');tn.image=n;nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tn.outputs[0],nm.inputs['Color']);nt.links.new(nm.outputs[0],b.inputs['Normal'])
        met,rou=split_mask(t[:-4]+'_mask.png')
        if met:
            for im,inp in ((met,'Metallic'),(rou,'Roughness')):
                tm=nt.nodes.new('ShaderNodeTexImage');tm.image=im;nt.links.new(tm.outputs[0],b.inputs[inp])
        else:b.inputs['Metallic'].default_value=P.get('metallic',0.1);b.inputs['Roughness'].default_value=1-P.get('smoothness',0.3)
    else:
        b.inputs['Base Color'].default_value=tuple(col);b.inputs['Metallic'].default_value=P.get('metallic',0.1);b.inputs['Roughness'].default_value=1-P.get('smoothness',0.3)
    mats[k]=m;return m
tris=0
for bone,subs in read_fam(fam):
    V=[];N=[];U=[];F=[];FM=[];ml=[]
    for sb in subs:
        n=len(sb['pos'])//3;o=len(V)
        V+=[(-sb['pos'][3*i],-sb['pos'][3*i+2],sb['pos'][3*i+1]) for i in range(n)]   # Unity (x,y,z) -> Blender (-x,-z,y), front at -Y
        N+=[(-sb['nrm'][3*i],-sb['nrm'][3*i+2],sb['nrm'][3*i+1]) for i in range(n)];U+=[(sb['uv'][2*i],1+sb['uv'][2*i+1]) for i in range(n)]
        key=(sb['tex'] or '')+'|'+','.join(f'{x:.4f}' for x in sb['col']);m=material(sb['tex'],sb['col'],key)
        if m not in ml:ml.append(m)
        F+=[(o+sb['idx'][j],o+sb['idx'][j+1],o+sb['idx'][j+2]) for j in range(0,len(sb['idx']),3)];FM+=[ml.index(m)]*(len(sb['idx'])//3)
    me=bpy.data.meshes.new(bone or name);me.from_pydata(V,[],F)
    for m in ml:me.materials.append(m)
    me.polygons.foreach_set('material_index',FM);uv=me.uv_layers.new(name='UVMap');li=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',li)
    uv.data.foreach_set('uv',np.asarray(U,np.float32)[li].ravel());me.shade_smooth();me.normals_split_custom_set_from_vertices(N);me.validate(clean_customdata=False)
    ob=bpy.data.objects.new(bone or name,me);bpy.context.collection.objects.link(ob);tris+=len(F)
bpy.ops.export_scene.fbx(filepath=os.path.join(out,f'{name}.fbx'),path_mode='RELATIVE',embed_textures=False,mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False)
print('exported',name,'triangles',tris,'objects',len(bpy.data.objects),'materials',len(mats))
