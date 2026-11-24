"""Blue Dragon test infantry bodies (Osama 23 Nov 2026 17:3x PST, thread 1567745029781454889: "please get them in and put them in test infantry
squads", "just basic riflemen"). Method of pla-recon-frogsuit-20261122/tools/rig_frog.py: arms fitted to the native BA A-pose (arm_fit.ArmFit),
native US Ranger surface weights (nearest face, 4 influences), the 40 BA bones; output FAS1 lod0-2 at full resolution for atlas.py +
decimate_fas.py. Two sources:
- kr: cgmodel 785245 'South Korea soldier' (SK_SouthKoreaSoldier.fbx, UE-style 60-bone rig): coat + arms fitted from its own skeleton,
  head/helmet rigid Head, vest rigid Spine2. The T65A2 rifle (SM_T65A2.fbx) is left out: the squad carries the game weapon.
- jp: cgmodel 803757 'jap' (jap.FBX, one static A-pose mesh, no skeleton): centred, standing on z=0; arm landmarks are estimated from the
  arm vertices (principal axis, native segment proportions) and only vertices near that axis are fitted.
usage: blender -b -P rig_bd.py -- kr|jp SOURCE.fbx TEXDIR DONOR.glb OUT"""
import json,struct,sys,io
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-five-specs-repo/tools/pla-infantry')
from arm_fit import ArmFit,rotation_between
mode,src,texdir,donor_glb,out=sys.argv[sys.argv.index('--')+1:];texdir=Path(texdir).resolve();out=Path(out).resolve();KEY='bd_'+mode
FLAT=str(texdir.parent/'flat_n.png')
CFG={'kr':{'meshes':['SM_SKCoat','SM_CC_Arm','SM_SKPants','SM_bootBlackLeather','SM_SKVest','SM_SkmanHead','SM_helmetSouthKorea'],
           'fit':('SM_SKCoat','SM_CC_Arm'),'rigid':{'SM_SkmanHead':'Head','SM_helmetSouthKorea':'Head','SM_SKVest':'Spine2'},
           'tex':{'M_SKCoat':('T_SKCoat_Color','T_SKCoat_Normal'),'M_CC_Arm':('T_CC_Arm_color','T_CC_Arm_Normal'),'M_SKPants':('T_SKPants_Color','T_SKPants_Normal'),
                  'M_bootBlackLeather':('T_bootBlackLeather_Color',None),'M_SKVest':('T_SKVest_Color',None),'M_SkmanHead':('T_SkmanHead_Color','T_SKmanHead_Normal'),
                  'M_helmetSouthKorea':('T_helmetSouthKorea_Color',None)}},
     # the FBX's own texture links: material names do not match the texture numbers
     'jp':{'tex':{f'jap_0{m}':(f'jap_0{t}_BaseColor',f'jap_0{t}_Normal') for m,t in ((1,2),(2,5),(3,3),(4,4),(5,1))}}}[mode]
def find(stem):
    if stem is None:return FLAT
    for e in ('.png','.PNG','.jpg','.tga'):
        if (texdir/(stem+e)).exists():return str(texdir/(stem+e))
    raise FileNotFoundError(stem)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=donor_glb,bone_heuristic='TEMPERANCE')
na=next(o for o in bpy.data.objects if o.type=='ARMATURE');native={b.name:list(na.matrix_world@b.head_local) for b in na.data.bones}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=src)
objs={o.name:o for o in bpy.data.objects if o.type=='MESH'}
parts=[objs[n] for n in CFG['meshes']] if mode=='kr' else list(objs.values())
sa=next((o for o in bpy.data.objects if o.type=='ARMATURE'),None)
source={b.name:list(sa.matrix_world@b.head_local) for b in sa.data.bones} if sa else None
W={o.name:o.matrix_world.copy() for o in parts}   # before the armature (their parent) is removed
for o in parts:o.parent=None;o.matrix_world=W[o.name]
for o in list(bpy.data.objects):
    if o not in parts:bpy.data.objects.remove(o,do_unlink=True)
for o in parts:
    ch=o.data.uv_layers.active
    for l in list(o.data.uv_layers):
        if l!=ch:o.data.uv_layers.remove(l)
    ch.name='BA_DiffuseUV';o.data.uv_layers.active_index=0
    for m in list(o.modifiers):o.modifiers.remove(m)
    if o.data.shape_keys:o.shape_key_clear()
    o.animation_data_clear()   # FBX object tracks re-apply the old location on every frame change
    # Bake the full world matrix (incl. delta transforms and any parent space) into the vertices; the object ends at identity.
    mw=o.matrix_world.copy();o.data.transform(mw);o.data.update();o.delta_location=(0,0,0);o.delta_rotation_euler=(0,0,0);o.delta_scale=(1,1,1);o.matrix_world=mw.__class__.Identity(4)
fitaudit=None
if mode=='kr':
    fit=ArmFit(source,native,0.0);fitaudit=fit.audit
    for o in parts:
        if o.name in CFG['fit']:
            c=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',c);c=fit.deform(c.reshape(-1,3));o.data.vertices.foreach_set('co',c.ravel())
else:
    o=parts[0];c=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',c);P=c.reshape(-1,3)
    P=P-[ (P[:,0].min()+P[:,0].max())/2,(P[:,1].min()+P[:,1].max())/2,P[:,2].min()]
    nat=lambda n:np.asarray(native[n],float)
    L1=np.linalg.norm(nat('LeftForeArm')-nat('LeftArm'));L2=np.linalg.norm(nat('LeftHand')-nat('LeftForeArm'));L3=0.19
    src={};axes={}
    for sfx,side,sign in (('l','Left',1),('r','Right',-1)):
        A=P[(sign*P[:,0]>0.30)&(P[:,2]>0.9)];m=A.mean(0);d=np.linalg.svd(A-m)[2][0]
        if sign*d[0]<0:d=-d
        ts=(nat(side+"Arm")[0]-m[0])/d[0];S=m+d*ts;tip=((A-m)@d).max();Lt=tip-ts   # shoulder joint at the native LeftArm/RightArm x
        E=S+d*Lt*L1/(L1+L2+L3);Wr=S+d*Lt*(L1+L2)/(L1+L2+L3)
        R=rotation_between(Wr-E,nat(side+'Hand')-nat(side+'ForeArm'))
        src['upperarm_'+sfx]=S;src['lowerarm_'+sfx]=E;src['hand_'+sfx]=Wr
        for f,F in (('index','Index'),('ring','Ring'),('thumb','Thumb')):src[f+'_01_'+sfx]=Wr+R.T@(nat(side+'Hand'+F+'1')-nat(side+'Hand'))
        axes[sign]=(S,d,Lt)
    fit=ArmFit(src,native,0.0);fitaudit=fit.audit+[{'estimated_landmarks':{k:[round(float(x),3) for x in v] for k,v in src.items()}}]
    F=fit.deform(P);mask=np.zeros(len(P))
    for sign,(S,d,Lt) in axes.items():
        t=(P-S)@d;dist=np.linalg.norm((P-S)-t[:,None]*d,axis=1)
        mask=np.maximum(mask,(1-smooth((dist-0.10)/0.05))*smooth((t+0.05)/0.05)*(sign*P[:,0]>0))
    P=P+(F-P)*mask[:,None];o.data.vertices.foreach_set('co',P.ravel());o.data.update()
textures={}
for o in parts:
    for mat in o.data.materials:
        base,nrm=CFG['tex'][mat.name]
        mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
        if bs is None:bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');mat.node_tree.links.new(bs.outputs[0],mat.node_tree.nodes.get('Material Output').inputs[0])
        tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(find(base),check_existing=True);mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.nodes.active=tx
        textures[mat.name]={'base':find(base),'normal':find(nrm)}
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=donor_glb,bone_heuristic='TEMPERANCE');refs=[o for o in bpy.data.objects if o not in before]
arm=next(o for o in refs if o.type=='ARMATURE');donor=next(o for o in refs if o.type=='MESH' and o.name.startswith('lod_0'))
for o in parts:
    for g in list(o.vertex_groups):o.vertex_groups.remove(g)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    for g in donor.vertex_groups:o.vertex_groups.new(name=g.name)
    m=o.modifiers.new('w','DATA_TRANSFER');m.object=donor;m.use_vert_data=True;m.data_types_verts={'VGROUP_WEIGHTS'};m.vert_mapping='POLYINTERP_NEAREST';m.layers_vgroup_select_src='ALL';m.layers_vgroup_select_dst='NAME';bpy.ops.object.modifier_apply(modifier=m.name)
    rigid=CFG.get('rigid',{}).get(o.name)
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
audit={'unit':[],'key':KEY,'source':src if isinstance(src,str) else 'jap.FBX','textures':textures,'triangles':len(me.loop_triangles),'materials':[m.name for _,m in used],'arm_fit':fitaudit,'z':[min(zs),max(zs)]}
(folder/'configuration.json').write_text(json.dumps(audit,indent=2,default=float)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'rig.blend'))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='TEXTURE';s.display.shading.light='STUDIO';s.render.resolution_x=700;s.render.resolution_y=900
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam'));bpy.context.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.2
for i,loc in enumerate(((0,-5,0.95),(2.2,-5,1.2),(-2.5,4.5,1.2))):
    cam.location=loc;cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(folder/f'rest{i}.png');bpy.ops.render.render(write_still=True)
mw=[list(r) for r in obj.matrix_world];print('MW',mw)
print('RIGDONE',json.dumps({k:audit[k] for k in ('triangles','materials','z')},default=float))
