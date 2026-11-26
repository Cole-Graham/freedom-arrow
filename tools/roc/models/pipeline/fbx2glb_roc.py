"""Purchased ShuyangXi FBX + PBR textures -> GLB for famconv (Blender, background).
usage: blender -b -P fbx2glb.py -- IN.fbx OUT.glb TEXDIR COATING [DROP_REGEX]
COATING: '' (plain), 'Camo', 'Dust', 'DustCamo'. Each FBX material MAT uses TEXDIR/**/<prefix>_<MAT>[_COATING]_BaseColor.png
with the plain Metallic, Roughness, Normal and AO maps (only the colour changes between coatings)."""
import bpy,sys,re,glob,os
a=sys.argv[sys.argv.index('--')+1:];fbx,out,texdir,coat=a[:4];drop=a[4] if len(a)>4 else r'(?i)^plane|vray|light|camera|dummy|diban|ground|floor'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=fbx)
ANIM=[o.name for o in bpy.data.objects if o.animation_data and o.animation_data.action]
print('ANIMATED',ANIM)
for o in list(bpy.data.objects):
    if o.type=='MESH' and (re.search(drop,o.name) or any(m and re.search(drop,m.name) for m in o.data.materials)):
        for ch in list(o.children):
            mw=ch.matrix_world.copy();ch.parent=None;ch.matrix_world=mw
        bpy.data.objects.remove(o,do_unlink=True)
    elif o.type not in('MESH','EMPTY'):bpy.data.objects.remove(o,do_unlink=True)
import os as _os
# LOCALID (21 Nov 2026, ZTZ-96A hatch): parts whose vertices already sit in their parent's space but whose FBX node still carries a
# transform (ZTZ96A_MG: 180 deg about Z + (-142,46,-144) cm), which drops the hatch into the hull. Ignore that node's own transform.
for o in [o for o in bpy.data.objects if _os.environ.get('LOCALID') and __import__('re').search(_os.environ['LOCALID'],o.name)]:
    o.matrix_basis=__import__('mathutils').Matrix.Identity(4);o.matrix_parent_inverse=__import__('mathutils').Matrix.Identity(4);bpy.context.view_layer.update();print('LOCALID',o.name)
PROP=float(_os.environ.get('PROPFIX','0'))   # KJ-500: propellers exported at 438 m; scale meshes over 50 m to this size about their origin
if PROP:
    from mathutils import Vector
    bpy.context.view_layer.update()
    for o in [o for o in bpy.data.objects if o.type=='MESH']:
        bb=[o.matrix_world@Vector(c) for c in o.bound_box];ext=max(max(v[i] for v in bb)-min(v[i] for v in bb) for i in range(3))
        if ext>50:
            f=PROP/ext;o.matrix_world=o.matrix_world@__import__('mathutils').Matrix.Scale(f,4);print('PROPFIX',o.name,round(ext,1),'->',PROP)
OBJ=_os.environ.get('OBJFIX','')   # snap each FBX part to its OBJ counterpart (OBJ is baked in world space, cm); fixes guns placed by bad FBX pivots
if OBJ:
    from mathutils import Vector
    bpy.context.view_layer.update()
    fb={o.name:o for o in bpy.data.objects if o.type=='MESH'}
    def box(o,k=1.0):
        bb=[o.matrix_world@Vector(c) for c in o.bound_box];return Vector([min(v[i] for v in bb)*k for i in range(3)]),Vector([max(v[i] for v in bb)*k for i in range(3)])
    before=set(bpy.data.objects);bpy.ops.wm.obj_import(filepath=OBJ);objs=[o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    for o in objs:
        f=fb.get(re.sub(r'\.\d+$','',o.name))
        if f is not None:
            (a0,a1),(b0,b1)=box(f),box(o,0.01)
            if max(abs((a1-a0)[i]-(b1-b0)[i]) for i in range(3))<0.03:
                d=((b0+b1)-(a0+a1))/2
                if d.length>0.02:
                    for c in f.children_recursive:
                        mw=c.matrix_world.copy();c.parent=None;c.matrix_world=mw
                    mw=f.matrix_world.copy();mw.translation+=d;f.matrix_world=mw;bpy.context.view_layer.update();print('OBJFIX',f.name,[round(x,3) for x in d])
    for o in objs:bpy.data.objects.remove(o,do_unlink=True)
SHARP=float(_os.environ.get('SHARP','0'))   # degrees: split normals at edges sharper than this (seller meshes smoothed across hard corners look 'ballooned')
if SHARP:
    for o in [o for o in bpy.data.objects if o.type=='MESH']:
        bpy.context.view_layer.objects.active=o
        for x in bpy.context.selected_objects:x.select_set(False)
        o.select_set(True);bpy.ops.object.shade_smooth_by_angle(angle=__import__('math').radians(SHARP),keep_sharp_edges=True);print('SHARP',o.name,SHARP)
SHIFT=_os.environ.get('SHIFT','')   # 'REGEX=dx,dy,dz;...' world move (m) for parts with bad FBX offsets and no OBJ to snap to
for spec in [x for x in SHIFT.split(';') if x]:
    rx,v=spec.rsplit('=',1);dv=[float(t) for t in v.split(',')]
    for o in [o for o in bpy.data.objects if o.type=='MESH' and re.search(rx,o.name)]:
        mw=o.matrix_world.copy();mw.translation.x+=dv[0];mw.translation.y+=dv[1];mw.translation.z+=dv[2];o.matrix_world=mw;bpy.context.view_layer.update();print('SHIFT',o.name,dv)
files=glob.glob(os.path.join(texdir,'**','*.png'),recursive=True)
def _find(key,kind,coating):
    pat=('_'+coating.lower() if coating else '')+'_'+kind.lower()+'.png'
    c=[f for f in files if os.path.basename(f).lower().endswith(pat) and re.search(r'(^|_)'+re.escape(key)+r'_',os.path.basename(f).lower().replace(' ','')) and 'nologo' not in f.lower() and '/navy/' not in f.lower()]
    if coating=='':c=[f for f in c if not re.search(r'_(camo|dust|dustcamo|desert|mix|yellow|green|black)_'+kind.lower()+r'\.png$',os.path.basename(f).lower())]
    return min(c,key=len) if c else None
def find(mat,kind,coating=''):
    key=re.sub(r'(_(dustcamo|dust_camo|camo|dust|dig|yellow_mix|green_mix|mix|yellow|green|black))+$','',mat.lower().replace(' ',''))
    keys=[key];k=key
    while '_' in k and kind!='Opacity':k=k.rsplit('_',1)[0];keys.append(k)   # ROC copy (26 Nov): an opacity map must match its own material, not a sibling's (M60A3 body got the net's)
    for k in keys:
        for co in ([coating,''] if coating else ['']):
            f=_find(k,kind,co)
            if f:return f
    if kind=='Opacity':return None
    last=key.rsplit('_',1)[-1]           # Mig21_Hull -> any *_Hull_<kind> (J7D_Hull)
    for co in ([coating,''] if coating else ['']):
        f=_find(last,kind,co)
        if f:return f
    return None
def gltf_out():
    g=bpy.data.node_groups.get('glTF Material Output')
    if g:return g
    g=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');g.interface.new_socket('Occlusion',in_out='INPUT',socket_type='NodeSocketFloat');return g
report=[]
for m in bpy.data.materials:
    name=m.name.split('.')[0];bc=find(name,'BaseColor',coat) or find(name,'BaseColor')
    if bc is None:report.append((name,'NO TEXTURES'));continue
    m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');b=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(b.outputs[0],o.inputs[0])
    def tex(path,data):
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(path)
        if data:t.image.colorspace_settings.name='Non-Color'
        return t
    op=find(name,'Opacity')
    if op:   # merge the author's opacity map into the colour alpha (cutout); famconv keeps RGBA, build_all marks MASK
        import numpy as _np
        ci=bpy.data.images.load(bc);ai=bpy.data.images.load(op);w,h=ci.size
        if tuple(ai.size)!=(w,h):ai.scale(w,h)
        px=_np.empty(w*h*4,_np.float32);ci.pixels.foreach_get(px);pa=_np.empty(w*h*4,_np.float32);ai.pixels.foreach_get(pa);px[3::4]=pa[0::4]
        bc2=os.path.join(os.path.dirname(out),os.path.basename(bc).replace('.png','_rgba.png'))
        ni=bpy.data.images.new('rgba_'+name,w,h,alpha=True);ni.pixels.foreach_set(px);ni.filepath_raw=bc2;ni.file_format='PNG';ni.save();bc=bc2
    tb=tex(bc,False);nt.links.new(tb.outputs[0],b.inputs['Base Color'])
    if op:nt.links.new(tb.outputs['Alpha'],b.inputs['Alpha'])
    got={'BaseColor':os.path.basename(bc),'Opacity':os.path.basename(op) if op else None}
    for kind,inp in(('Metallic','Metallic'),('Roughness','Roughness')):
        f=find(name,kind)
        if f:nt.links.new(tex(f,True).outputs[0],b.inputs[inp]);got[kind]=os.path.basename(f)
    f=find(name,'Normal')
    if f:n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(f,True).outputs[0],n.inputs['Color']);nt.links.new(n.outputs[0],b.inputs['Normal']);got['Normal']=os.path.basename(f)
    f=find(name,'AO')
    if f:gn=nt.nodes.new('ShaderNodeGroup');gn.node_tree=gltf_out();nt.links.new(tex(f,True).outputs[0],gn.inputs['Occlusion']);got['AO']=os.path.basename(f)
    report.append((name,got))
for r in report:print('MAT',r)
for o in bpy.data.objects:print('OBJ',o.type,o.name,'parent',o.parent.name if o.parent else '-')
from mathutils import Vector as _V
# FLATTEN: static models only; bake every mesh's world transform into its own mesh copy and export identity nodes,
# so FBX parent-inverse/unit-scale chains cannot re-offset or rescale parts in the glTF.
import mathutils as _mu
bpy.context.view_layer.update()
DX=_os.environ.get('DROPX','')   # extra parts to remove (floating source parts)
for o in [o for o in bpy.data.objects if DX and o.type=='MESH' and re.search(DX,o.name)]:print('DROPX',o.name);bpy.data.objects.remove(o,do_unlink=True)
_mw={o.name:o.matrix_world.copy() for o in bpy.data.objects}
for o in bpy.data.objects:o.animation_data_clear()
for o in [o for o in bpy.data.objects if o.type=='MESH']:
    o.data=o.data.copy();o.data.transform(_mw[o.name])
    if _mw[o.name].determinant()<0:o.data.flip_normals()
for o in bpy.data.objects:o.parent=None
for o in bpy.data.objects:o.matrix_world=_mu.Matrix.Identity(4)
bpy.context.view_layer.update()
_pts=[o.matrix_world@_V(c) for o in bpy.data.objects if o.type=='MESH' for c in o.bound_box]
if _pts:print('DIMS',*[round(max(p[i] for p in _pts)-min(p[i] for p in _pts),3) for i in range(3)])
bpy.ops.export_scene.gltf(filepath=out,export_animations=False,export_format='GLB',export_image_format='AUTO',export_apply=True)
print('WROTE',out)
