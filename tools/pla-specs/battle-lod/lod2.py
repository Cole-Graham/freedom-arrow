"""Battle LOD v2 (per loose piece): decimate a .fam to a triangle budget; any piece that changes size or loses surface is kept whole.
usage: blender -b -P lod2.py -- IN.fam OUT.fam TARGET_TRIS"""
import bpy,bmesh,sys,struct,math,os
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
a=sys.argv[sys.argv.index('--')+1:];src,dst,T=a[0],a[1],int(a[2])
parts=read_fam(src);KEEP=int(os.environ.get('KEEP','60'))
def area(sb):
    P=sb['pos'];I=sb['idx'];A=0.0
    for f in range(0,len(I),3):
        a,b,c=I[f],I[f+1],I[f+2];ux,uy,uz=P[3*b]-P[3*a],P[3*b+1]-P[3*a+1],P[3*b+2]-P[3*a+2];vx,vy,vz=P[3*c]-P[3*a],P[3*c+1]-P[3*a+1],P[3*c+2]-P[3*a+2]
        A+=0.5*math.sqrt((uy*vz-uz*vy)**2+(uz*vx-ux*vz)**2+(ux*vy-uy*vx)**2)
    return A
def bbox(sb):
    P=sb['pos'];return [(min(P[i::3]),max(P[i::3])) for i in range(3)]
def good(a,b):   # same extent (no lost barrels/antennas) and most of the surface kept (no holes)
    ea,eb=bbox(a),bbox(b);size=max(hi-lo for lo,hi in ea) or 1
    if max(abs(ea[i][j]-eb[i][j]) for i in range(3) for j in range(2))>0.02*size:return False
    return area(b)>=float(__import__('os').environ.get('AREAKEEP','0.8'))*area(a)
PLANAR_ON=True
def decimate(sb,r):
    nt=len(sb['idx'])//3
    P=sb['pos'];UV=sb['uv'];I=sb['idx'];nv=len(P)//3
    key={};vid=[];verts=[]
    for i in range(nv):   # weld split vertices (same position and UV) so the decimator sees one surface per UV island
        k=(round(P[3*i],5),round(P[3*i+1],5),round(P[3*i+2],5))+((round(UV[2*i],4),round(UV[2*i+1],4)) if os.environ.get('WELDUV','0')=='1' else ())   # keep UV seams: an island edge stays a mesh edge
        if k not in key:key[k]=len(verts);verts.append((P[3*i],P[3*i+1],P[3*i+2]))
        vid.append(key[k])
    faces=[];fuv=[]
    for f in range(nt):
        tri=(I[3*f],I[3*f+1],I[3*f+2]);w=tuple(vid[j] for j in tri)
        if len(set(w))<3:continue
        faces.append(w);fuv.append([(UV[2*j],UV[2*j+1]) for j in tri])
    me=bpy.data.meshes.new('m');me.from_pydata(verts,[],faces)
    assert len(me.polygons)==len(fuv),('face count changed',len(me.polygons),len(fuv))   # UVs below are matched by face order
    uvl=me.uv_layers.new(name='UV')
    for pi,poly in enumerate(me.polygons):
        if pi>=len(fuv):break
        for c,li in enumerate(poly.loop_indices):uvl.data[li].uv=fuv[pi][c]
    ob=bpy.data.objects.new('o',me);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob
    # 1) merge flat areas without crossing UV islands (keeps texture mapping exact); 2) collapse the rest down to the budget
    if PLANAR_ON:
        pl=ob.modifiers.new('p','DECIMATE');pl.decimate_type='DISSOLVE';pl.angle_limit=math.radians(float(__import__('os').environ.get('PLANAR','3')));pl.delimit={'UV','SEAM','SHARP'}
        bpy.ops.object.modifier_apply(modifier='p')
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free()
    left=len(me.polygons);want=max(1,int(nt*r))
    if left>want:
        md=ob.modifiers.new('d','DECIMATE');md.decimate_type='COLLAPSE';md.ratio=want/left;md.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier='d')
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    me.set_sharp_from_angle(angle=math.radians(40))
    cn=me.corner_normals;uvd=me.uv_layers['UV'].data
    vb={};pos=[];nrm=[];uv=[];idx=[]
    for poly in me.polygons:
        for li in poly.loop_indices:
            v=me.loops[li].vertex_index;n=cn[li].vector;u=uvd[li].uv
            k=(v,round(n.x,3),round(n.y,3),round(n.z,3),round(u.x,5),round(u.y,5))
            if k not in vb:vb[k]=len(pos)//3;co=me.vertices[v].co;pos+= [co.x,co.y,co.z];nrm+=[n.x,n.y,n.z];uv+=[u.x,u.y]
            idx.append(vb[k])
    res=dict(tex=sb['tex'],col=sb['col'],pos=pos,nrm=nrm,uv=uv,idx=idx)
    bpy.data.objects.remove(ob);bpy.data.meshes.remove(me)
    return res
def pieces(sb):   # loose pieces by shared positions
    P=sb['pos'];I=sb['idx'];par={}
    def find(x):
        while par.setdefault(x,x)!=x:par[x]=par[par[x]];x=par[x]
        return x
    key=[(round(P[3*i],5),round(P[3*i+1],5),round(P[3*i+2],5)) for i in range(len(P)//3)]
    for f in range(0,len(I),3):
        r0=find(key[I[f]])
        for j in (1,2):
            r1=find(key[I[f+j]])
            if r1!=r0:par[r1]=r0
    grp={}
    for f in range(0,len(I),3):grp.setdefault(find(key[I[f]]),[]).append(f)
    out=[]
    for fs in grp.values():
        m={};pos=[];nrm=[];uv=[];idx=[]
        for f in fs:
            for v in I[f:f+3]:
                if v not in m:m[v]=len(pos)//3;pos+=P[3*v:3*v+3];nrm+=sb['nrm'][3*v:3*v+3];uv+=sb['uv'][2*v:2*v+2]
                idx.append(m[v])
        out.append(dict(tex=sb['tex'],col=sb['col'],pos=pos,nrm=nrm,uv=uv,idx=idx))
    return out
PCS=[(bi,si,pc) for bi,(bone,ss) in enumerate(parts) for si,sb in enumerate(ss) for pc in pieces(sb)]
# Battle-distance culling: loose pieces smaller than CULL x the model's largest side (bolts, rivets, handles) are left out.
allb=[c for _,_,pc in PCS for c in [bbox(pc)]];ext=[(min(b[i][0] for b in allb),max(b[i][1] for b in allb)) for i in range(3)];L=max(hi-lo for lo,hi in ext)
CULL=float(os.environ.get('CULL','0.015'));diag=lambda pc:max(hi-lo for lo,hi in bbox(pc))
small=lambda x:diag(x[2])<CULL*L
# A part made mostly of small pieces (track links, tyre tread, grilles) is structure, not clutter: keep its pieces.
sa={};ta={}
for x in PCS:
    k=(x[0],x[1]);A=area(x[2]);ta[k]=ta.get(k,0)+A
    if small(x):sa[k]=sa.get(k,0)+A
struct_=lambda x:sa.get((x[0],x[1]),0)>float(os.environ.get('STRUCT','0.35'))*ta[(x[0],x[1])]
cut=[x for x in PCS if small(x) and not struct_(x)];PCS=[x for x in PCS if not small(x) or struct_(x)]
print('LOD culled pieces',len(cut),'triangles',sum(len(x[2]['idx'])//3 for x in cut),flush=True)
N=[len(pc['idx'])//3 for _,_,pc in PCS];AR=[area(pc) for _,_,pc in PCS];tot=sum(N)
def budget(d):return sum(n if n<=KEEP else min(n,max(KEEP,d*a)) for n,a in zip(N,AR))
lo,hi=0.0,max(n/max(a,1e-9) for n,a in zip(N,AR))+1
for _ in range(60):
    mid=(lo+hi)/2
    if budget(mid)>T:hi=mid
    else:lo=mid
D=lo;print('LOD total',tot,'pieces',len(PCS),'density',round(D,2),flush=True)
TOL=float(os.environ.get('TOL','0.006'))
def good(a,b):   # v2: extent within max(2% of the piece, TOL of the model); most of the surface kept
    ea,eb=bbox(a),bbox(b);size=max(hi-lo for lo,hi in ea) or 1
    if max(abs(ea[i][j]-eb[i][j]) for i in range(3) for j in range(2))>max(0.02*size,TOL*L):return False
    return area(b)>=float(os.environ.get('AREAKEEP','0.7'))*area(a)
failed=[0,0]
res={}
for (bi,si,pc),n,a in zip(PCS,N,AR):
    r=1.0 if n<=KEEP else min(1.0,max(KEEP,D*a)/n);got=pc
    if r<0.999:
        rr=r
        for _ in range(6):
            cand=decimate(pc,rr)
            if good(pc,cand):got=cand;break
            PLANAR_ON=False;cand=decimate(pc,rr);PLANAR_ON=True   # double-sided panels: the planar merge can eat one side
            if good(pc,cand):got=cand;break
            if os.environ.get('DEBUG') and n>2000:
                ea,eb=bbox(pc),bbox(cand);sz=max(h-l for l,h in ea);print('FAIL n',n,'r',round(rr,3),'got',len(cand['idx'])//3,'bbdev',round(max(abs(ea[i][j]-eb[i][j]) for i in range(3) for j in range(2))/sz,3),'area',round(area(cand)/max(area(pc),1e-9),3),flush=True)
            rr=min(1.0,rr*1.5)
            if rr>=0.999:break
    if got is pc and r<0.999:failed[0]+=1;failed[1]+=n
    res.setdefault((bi,si),[]).append(got)
print('LOD kept whole (failed check)',failed,flush=True)
out=[]
for bi,(bone,ss) in enumerate(parts):
    nss=[]
    for si,sb in enumerate(ss):
        pos=[];nrm=[];uv=[];idx=[]
        for pc in res.get((bi,si),[]):
            o=len(pos)//3;pos+=list(pc['pos']);nrm+=list(pc['nrm']);uv+=list(pc['uv']);idx+=[o+i for i in pc['idx']]
        nss.append(dict(tex=sb['tex'],col=sb['col'],pos=pos,nrm=nrm,uv=uv,idx=idx))
    out.append((bone,nss))
def w_s(f,s):b=s.encode();f.write(struct.pack('<i',len(b)));f.write(b)
with open(dst,'wb') as f:
    f.write(b'FAM1');f.write(struct.pack('<i',len(out)))
    for bone,ss in out:
        w_s(f,bone);f.write(struct.pack('<i',len(ss)))
        for sb in ss:
            w_s(f,sb['tex']);f.write(struct.pack('<4f',*sb['col']));nv=len(sb['pos'])//3;f.write(struct.pack('<i',nv))
            f.write(struct.pack('<%df'%(3*nv),*sb['pos']));f.write(struct.pack('<%df'%(3*nv),*sb['nrm']));f.write(struct.pack('<%df'%(2*nv),*sb['uv']))
            f.write(struct.pack('<i',len(sb['idx'])));f.write(struct.pack('<%di'%len(sb['idx']),*sb['idx']))
nt=sum(len(sb['idx'])//3 for _,ss in out for sb in ss);print('LOD done',tot,'->',nt,flush=True)
