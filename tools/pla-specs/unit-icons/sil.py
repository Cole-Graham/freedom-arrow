"""Silhouette + detail lines of a .fam for a vanilla-style unit icon. Unity (x,y,z)->Blender(-x,-z,y): front is -Y.
Orthographic camera; AZ 0 = pure side view from -X (front points right, as vanilla ground/heli labels), AZ>0 turns toward the
front, EL lifts the camera (vanilla jet labels are 3/4 views). White emission body on transparent film, Freestyle lines black."""
import bpy,sys,os,math
from mathutils import Vector
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
a=sys.argv[sys.argv.index('--')+1:];fam,out=a[0],a[1];AZ=float(a[2]) if len(a)>2 else 0;EL=float(a[3]) if len(a)>3 else 0
bpy.ops.wm.read_factory_settings(use_empty=True);allp=[]
mat=bpy.data.materials.new('white');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1);em.inputs[1].default_value=1;o_=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],o_.inputs[0])
MODE=os.environ.get('MODE','sil');import json
# SKIP: sub-mesh numbers to leave out, e.g. landing gear ('11-44,53-55')
GLASSSUBS={int(x) for x in os.environ.get('GLASSSUBS','').split(',') if x}   # sub-meshes to treat as glass (J-20: closed cockpit frame instead of the raised canopy)
_r=os.environ.get('ROTSUB','')   # e.g. '147-149:2.45,3.99,-23.7'
ROTS={i:tuple(map(float,_r.split(':')[1].split(','))) for i in range(int(_r.split(':')[0].split('-')[0]),int(_r.split(':')[0].split('-')[-1])+1)} if _r else {}
SKIP={i for part in os.environ.get('SKIP','').split(',') if part for i in (range(int(part.split('-')[0]),int(part.split('-')[-1])+1))}
mj=json.load(open(fam[:-4]+'.mat.json')) if os.path.exists(fam[:-4]+'.mat.json') else {}
black=bpy.data.materials.new('black');black.use_nodes=True;bn=black.node_tree;bn.nodes.clear();be=bn.nodes.new('ShaderNodeEmission');be.inputs[0].default_value=(0,0,0,1);bo=bn.nodes.new('ShaderNodeOutputMaterial');bn.links.new(be.outputs[0],bo.inputs[0])
texm={}
def matfor(sb):
    key=(sb['tex'] or '')+'|'+','.join(f'{x:.4f}' for x in sb['col']);m=mj.get(key) or mj.get(sb['tex']) or {}
    glass=bool(sb.get('_glass')) if os.environ.get('ONLYSUBS') else bool(m.get('cockpitDonor') or m.get('clearGlass') or sb.get('_glass'))
    if not os.environ.get('ONLYSUBS') and os.environ.get('GLASSBLEND') and m.get('alpha')=='BLEND' and (not sb['tex'] or 'canopy' in sb['tex'].lower()):glass=True   # untextured see-through parts (Z-10K canopy)
    if MODE=='glass':return mat if glass else black
    if MODE=='albedo' and sb['tex'] and os.path.exists(os.path.join(os.path.dirname(fam),sb['tex'])):
        if sb['tex'] not in texm:
            tm=bpy.data.materials.new(sb['tex']);tm.use_nodes=True;nt2=tm.node_tree;nt2.nodes.clear();e2=nt2.nodes.new('ShaderNodeEmission');tx=nt2.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(os.path.join(os.path.dirname(fam),sb['tex']))
            o2=nt2.nodes.new('ShaderNodeOutputMaterial');nt2.links.new(tx.outputs[0],e2.inputs[0]);nt2.links.new(e2.outputs[0],o2.inputs[0]);texm[sb['tex']]=tm
        return texm[sb['tex']]
    return mat
FAMD=list(read_fam(fam))
GEAR=os.environ.get('GEARCUT')=='1'
if GEAR:   # landing gear = small loose parts hanging at the bottom of the model (wheels, struts, doors)
    _all=[(sb['pos'][3*i],sb['pos'][3*i+1],sb['pos'][3*i+2]) for _,ss in FAMD for sb in ss for i in range(len(sb['pos'])//3)]
    gy0=min(p[1] for p in _all);gH=max(p[1] for p in _all)-gy0;gL=max(max(p[2] for p in _all)-min(p[2] for p in _all),max(p[0] for p in _all)-min(p[0] for p in _all))
    GTOP=float(os.environ.get('GEARTOP','0.3'));gearfaces=0
def drop_gear(sb,F):
    global gearfaces
    pos=sb['pos'];key=[(round(pos[3*i],3),round(pos[3*i+1],3),round(pos[3*i+2],3)) for i in range(len(pos)//3)]
    par={}
    def find(a):
        while par.setdefault(a,a)!=a:par[a]=par[par[a]];a=par[a]
        return a
    for f in F:
        a=find(key[f[0]])
        for v in f[1:]:
            b=find(key[v])
            if a!=b:par[b]=a
    isl={}
    for f in F:isl.setdefault(find(key[f[0]]),[]).append(f)
    keep=[]
    for fs in isl.values():
        vs=[key[v] for f in fs for v in f];ys=[v[1] for v in vs]
        ext=max(max(v[0] for v in vs)-min(v[0] for v in vs),max(v[2] for v in vs)-min(v[2] for v in vs))
        if max(ys)<gy0+GTOP*gH and min(ys)<gy0+0.06*gH and ext<0.25*gL:gearfaces+=len(fs);continue
        keep+=fs
    return keep
for bone,subs in FAMD:
    for k,sb in enumerate(subs):
        if k in SKIP:continue
        sb['_glass']=k in GLASSSUBS
        if k in ROTS:   # ROTSUB: close a canopy modelled open, rotating it about its hinge (Unity y,z) by deg
            hy,hz,deg=ROTS[k];ca,sa=math.cos(math.radians(deg)),math.sin(math.radians(deg));q=list(sb['pos'])
            for i in range(len(q)//3):
                dz,dy=q[3*i+2]-hz,q[3*i+1]-hy;q[3*i+2]=hz+dz*ca-dy*sa;q[3*i+1]=hy+dz*sa+dy*ca
            sb=dict(sb,pos=q)
        n=len(sb['pos'])//3;V=[(-sb['pos'][3*i],-sb['pos'][3*i+2],sb['pos'][3*i+1]) for i in range(n)];allp+=V
        F=[tuple(sb['idx'][j:j+3]) for j in range(0,len(sb['idx']),3)]
        if GEAR:F=drop_gear(sb,F)
        if MODE=='glass' and os.environ.get('GLASSONLY') and matfor(sb) is not mat:continue   # glass seen through an opaque canopy shell (J-20S)
        me=bpy.data.meshes.new(f'{bone}{k}');me.from_pydata(V,[],F)
        if MODE=='albedo':
            uvl=me.uv_layers.new()
            for poly in me.polygons:
                for li in poly.loop_indices:vi=me.loops[li].vertex_index;uvl.data[li].uv=(sb['uv'][2*vi],1+sb['uv'][2*vi+1])
        me.materials.append(matfor(sb))
        if MODE=='nose':   # NOSEZ: faces ahead of Unity z=NOSEZ white (nose cone), the rest black
            import bmesh;NZ=float(os.environ['NOSEZ']);bm=bmesh.new();bm.from_mesh(me)
            bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=(0,-NZ,0),plane_no=(0,1,0));bm.to_mesh(me);bm.free()
            me.materials.clear();me.materials.append(mat);me.materials.append(black)
            for poly in me.polygons:poly.material_index=0 if poly.center.y<-NZ else 1
        o=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(o)
xs=[p[0] for p in allp];ys=[p[1] for p in allp];zs=[p[2] for p in allp]
c=Vector(((min(xs)+max(xs))/2,(min(ys)+max(ys))/2,(min(zs)+max(zs))/2));size=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=4
if os.environ.get('LINES','0')!='1' and MODE=='sil':sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(1,1,1)
sc.render.film_transparent=True;sc.view_settings.view_transform='Standard'
sc.render.resolution_x=2400;sc.render.resolution_y=2400
sc.render.use_freestyle=os.environ.get('LINES','0')=='1';sc.render.line_thickness_mode='ABSOLUTE';sc.render.line_thickness=float(os.environ.get('LINE','4'))
ls=sc.view_layers[0].freestyle_settings;ls.crease_angle=math.radians(float(os.environ.get('CREASE','120')))
lset=ls.linesets[0] if ls.linesets else ls.linesets.new('L');lset.select_by_visibility=True;lset.select_silhouette=os.environ.get('SIL','1')=='1';lset.select_border=False;lset.select_crease=os.environ.get('CR','0')=='1'
if lset.linestyle is None:lset.linestyle=bpy.data.linestyles.new('LS')
lset.linestyle.color=(0,0,0)
d=Vector((-math.cos(math.radians(AZ))*math.cos(math.radians(EL)),-math.sin(math.radians(AZ))*math.cos(math.radians(EL)),math.sin(math.radians(EL))))
bpy.ops.object.camera_add(location=c+d*size*5);cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=size*1.1;cam.data.clip_end=size*20
t=cam.constraints.new('TRACK_TO');bpy.ops.object.empty_add(location=c);t.target=bpy.context.object;t.track_axis='TRACK_NEGATIVE_Z';t.up_axis='UP_Y'
sc.render.filepath=os.path.abspath(out);bpy.ops.render.render(write_still=True);print('size',round(size,2),'gearfaces',gearfaces if GEAR else 0)
