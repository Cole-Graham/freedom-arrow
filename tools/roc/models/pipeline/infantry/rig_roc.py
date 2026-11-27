"""rig_roc.py (25 Nov 2026, Shawn 10:2x "Can you start to work on infantry?"): ROC infantry bodies on the 40-bone BA soldier skeleton, by
rig_f1.py's method (ArmFit from the source rig's arm bones onto the native Ranger arms, native Ranger surface weights, rigid parts).
One body per run, chosen by KEY from roc_bodies.json. usage: blender -b -P rig_roc.py -- KEY CONFIG.json DONOR.glb OUT"""
import json,struct,sys,os
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-five-specs-repo/tools/pla-infantry')
from arm_fit import ArmFit
KEY,cfgp,donor_glb,out=sys.argv[sys.argv.index('--')+1:];out=Path(out);C=json.load(open(cfgp))[KEY]
src=C['source'];texdir=Path(C['texdir']);MESHES=C['meshes'];TEX={k:tuple(v) for k,v in C['tex'].items()};RIGID=C['rigid'];FIT=set(C['fit'])
FLAT=str(out/'flat_n.png')
def find(stem):
    if stem=='FLAT':return FLAT
    for e in ('.png','.PNG','.jpg','.tga'):
        if (texdir/(stem+e)).exists():return str(texdir/(stem+e))
        hit=sorted(texdir.rglob(stem+e))
        if hit:return str(hit[0])
    raise FileNotFoundError(stem)
out.mkdir(parents=True,exist_ok=True)
if not Path(FLAT).exists():
    im=bpy.data.images.new('flat',8,8);im.pixels=[0.5,0.5,1.0,1.0]*64;im.filepath_raw=FLAT;im.file_format='PNG';im.save()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=donor_glb,bone_heuristic='TEMPERANCE')
na=next(o for o in bpy.data.objects if o.type=='ARMATURE');native={b.name:list(na.matrix_world@b.head_local) for b in na.data.bones}
_d=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('lod_0'));NV=np.array([_d.matrix_world@v.co for v in _d.data.vertices])
import math
from mathutils import Euler,Matrix
if src.endswith('.blend'):bpy.ops.wm.open_mainfile(filepath=src)
else:bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=src)
def move_all(M):   # every top-level object, so children (meshes, bones) follow
    for o in [o for o in bpy.data.objects if o.parent is None]:o.matrix_world=M@o.matrix_world
    bpy.context.view_layer.update()
objs={o.name:o for o in bpy.data.objects if o.type=='MESH'};parts=[objs[n] for n in MESHES]
def pverts(names=None):return np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in parts if names is None or o.name in names])
if C.get('scale'):move_all(Matrix.Scale(C['scale'],4))
if C.get('rot'):move_all(Euler([math.radians(x) for x in C['rot']]).to_matrix().to_4x4())   # sources lying down: turn so up is +Z
if C.get('ground'):move_all(Matrix.Translation((0,0,-pverts()[:,2].min())))
if C.get('height'):move_all(Matrix.Scale(C['height']/pverts()[:,2].max(),4))
fitnative=dict(native)
if C.get('landmarks')=='auto':   # no skeleton: same mesh estimator on source and native Ranger, so its biases cancel
    sys.path.insert(0,str(Path(__file__).resolve().parent));import lm_auto
    source=lm_auto.estimate(pverts(C.get('lm_meshes')),hands=pverts([C['hand_mesh']]) if C.get('hand_mesh') else None);est_n=lm_auto.estimate(NV)
    for s_,side in (('l','Left'),('r','Right')):
        for k,n in (('upperarm','Arm'),('lowerarm','ForeArm'),('hand','Hand'),('index_01','HandIndex1'),('ring_01','HandRing1'),('thumb_01','HandThumb1')):fitnative[side+n]=est_n[k+'_'+s_]
else:
    BR=Euler([math.radians(x) for x in C.get('bonerot',[0,0,0])]).to_matrix().to_4x4()   # FBX armatures whose bones lie off the mesh frame
    sa=next(o for o in bpy.data.objects if o.type=='ARMATURE');_b={b.name:list(BR@sa.matrix_world@b.head_local) for b in sa.data.bones}
    source={k:_b[v] for k,v in C['bones'].items()}
print('LANDMARKS',json.dumps({k:[round(x,3) for x in v] for k,v in source.items()}))
fit=ArmFit(source,fitnative,0.0)
LM=dict(source)
W={o.name:o.matrix_world.copy() for o in parts}   # before the armature (their parent) is removed
for o in parts:o.parent=None;o.matrix_world=W[o.name]
for o in list(bpy.data.objects):
    if o not in parts:bpy.data.objects.remove(o,do_unlink=True)
textures={}
for o in parts:
    ch=o.data.uv_layers.active
    for l in list(o.data.uv_layers):
        if l!=ch:o.data.uv_layers.remove(l)
    ch.name='BA_DiffuseUV';o.data.uv_layers.active_index=0
    for m in list(o.modifiers):o.modifiers.remove(m)
    if o.data.shape_keys:o.shape_key_clear()   # with shape keys the basis key overrides vertex edits, so the arm fit was lost (SF 1)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    if o.name in C.get('decimate',{}):   # very heavy parts (helmet scans) cut before the body LODs share the budget
        n0=len(o.data.polygons);m=o.modifiers.new('cut','DECIMATE');m.ratio=min(1,C['decimate'][o.name]/max(1,sum(len(p.vertices)-2 for p in o.data.polygons)));bpy.ops.object.modifier_apply(modifier=m.name);print('PRECUT',o.name,n0,'->',len(o.data.polygons))
    if o.name in FIT:
        c=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',c);c=fit.deform(c.reshape(-1,3));o.data.vertices.foreach_set('co',c.ravel())
    if o.name in C.get('hand_meshes',[]):   # separate hand meshes hang below ArmFit's z>0.86 cut: move each side whole with its rigid hand transform
        c=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',c);c=c.reshape(-1,3)
        for sign,src_,dst_,seg_,hand_ in fit.sides:
            m=sign*c[:,0]>0;c[m]=dst_[2]+(c[m]-src_[2])@hand_.T
        o.data.vertices.foreach_set('co',c.ravel())
    for mat in o.data.materials:
        t=TEX[mat.name];base,nrm=(t if isinstance(t,tuple) else (t+'_Color',t+'_Normal'))
        mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
        if bs is None:bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');mat.node_tree.links.new(bs.outputs[0],mat.node_tree.nodes.get('Material Output').inputs[0])
        tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(find(base),check_existing=True);mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.nodes.active=tx
        textures[mat.name]={'base':find(base),'normal':find(nrm)}
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.render.resolution_x=900;s.render.resolution_y=700
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.6
dots=[];(out/KEY).mkdir(parents=True,exist_ok=True)
for k,v in LM.items():   # landmark check picture, before the arm fit moves anything
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.012,location=v);d=bpy.context.object;mt=bpy.data.materials.new('dot');mt.diffuse_color=(1,0,0,1) if 'arm' in k or 'hand' in k else (0,.4,1,1);d.data.materials.append(mt);dots.append(d)
s.display.shading.color_type='MATERIAL'
for i,(loc,tgt) in enumerate((((0,-4,1.25),(0,0,1.25)),((0,0,5),(0,0,1.25)))):
    cam.location=loc;cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/KEY/f'landmarks{i}.png');(os.environ.get('NORENDER') or bpy.ops.render.render(write_still=True))   # NORENDER=1: no diagnostic renders (renders run on Vengeance, 26 Nov)
s.display.shading.color_type='TEXTURE'
for d in dots:bpy.data.objects.remove(d,do_unlink=True)
bpy.data.objects.remove(cam,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=donor_glb,bone_heuristic='TEMPERANCE');refs=[o for o in bpy.data.objects if o not in before]
arm=next(o for o in refs if o.type=='ARMATURE');donor=next(o for o in refs if o.type=='MESH' and o.name.startswith('lod_0'))
for o in parts:
    for g in list(o.vertex_groups):o.vertex_groups.remove(g)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    for g in donor.vertex_groups:o.vertex_groups.new(name=g.name)
    m=o.modifiers.new('w','DATA_TRANSFER');m.object=donor;m.use_vert_data=True;m.data_types_verts={'VGROUP_WEIGHTS'};m.vert_mapping='POLYINTERP_NEAREST';m.layers_vgroup_select_src='ALL';m.layers_vgroup_select_dst='NAME';bpy.ops.object.modifier_apply(modifier=m.name)
    rigid=RIGID.get(o.name)
    if rigid=='torso':   # 27 Nov (Shawn's in-game shots): a vest rigid on Spine2 kept its lower edge with the chest while the hips turned, so it
        # swung out (marine side flap) or opened a black gap at the belly (ROC Infantry). Body weights, but never arm, hand or head bones.
        drop=[g for g in o.vertex_groups if any(k in g.name for k in ('Arm','Hand','Thumb','Index','Middle','Ring','Pinky','Head'))]
        for g in drop:o.vertex_groups.remove(g)
        lone=[v.index for v in o.data.vertices if not any(x.weight>0 for x in v.groups)]
        if lone:(o.vertex_groups.get('Spine2') or o.vertex_groups.new(name='Spine2')).add(lone,1,'REPLACE')
        rigid=None
    if rigid:
        for g in o.vertex_groups:g.remove(list(range(len(o.data.vertices))))
        o.vertex_groups[rigid].add(list(range(len(o.data.vertices))),1,'REPLACE')
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4);bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
    m=o.modifiers.new('BA animation','ARMATURE');m.object=arm;o.parent=arm
for o in refs:
    if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.name=KEY
names=[b.name for b in arm.data.bones];ni={n:i for i,n in enumerate(names)};assert len(names)==40
def ws(f,s):b=s.encode();f.write(struct.pack('<i',len(b))+b)
def xyz(v):return (-v.x,v.z,-v.y)
me=obj.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
used=[(i,m) for i,m in enumerate(me.materials) if any(t.material_index==i for t in me.loop_triangles)]
bad=[v.index for v in me.vertices if not any(g.weight>0 for g in v.groups)];assert not bad,len(bad)
folder=out/KEY;folder.mkdir(parents=True,exist_ok=True)
buf=bytearray()
import io
f=io.BytesIO();f.write(b'FAS1'+struct.pack('<i',len(names)))
for n in names:ws(f,n)
f.write(struct.pack('<i',len(used)))
for mi,mat in used:
    loops=[li for t in me.loop_triangles if t.material_index==mi for li in t.loops];ws(f,mat.name);f.write(struct.pack('<i',len(loops)))
    for li in loops:
        lp=me.loops[li];v=me.vertices[lp.vertex_index];u=uv[li].uv
        gs=sorted([(ni[obj.vertex_groups[g.group].name],g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])[:4];tot=sum(w for _,w in gs);gs=[(i,w/tot) for i,w in gs]+[(0,0)]*(4-len(gs))
        f.write(struct.pack('<8f4i4f',*xyz(v.co),*xyz(lp.normal),u.x,u.y,*[i for i,w in gs],*[w for i,w in gs]))
    inds=[i for j in range(0,len(loops),3) for i in (j,j+2,j+1)];f.write(struct.pack('<i',len(inds))+struct.pack('<'+'i'*len(inds),*inds))
for lvl in range(3):(folder/f'lod{lvl}.fas').write_bytes(f.getvalue())
zs=[v.co.z for v in me.vertices]
audit={'landmarks':LM,'unit':C['units'],'key':KEY,'selected_objects':MESHES,'textures':textures,'triangles':len(me.loop_triangles),'materials':[m.name for _,m in used],'arm_fit':fit.audit,'z':[min(zs),max(zs)]}
(out/'configurations.json').write_text(json.dumps([audit],indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'rig.blend'))
s.render.resolution_x=700;s.render.resolution_y=900
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.2
for i,loc in enumerate(((2.2,-5,1.2),(-2.5,4.5,1.2))):
    cam.location=loc;cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/f'rest{i}.png');(os.environ.get('NORENDER') or bpy.ops.render.render(write_still=True))
print('RIGDONE',json.dumps({k:audit[k] for k in ('triangles','materials','z')}))
