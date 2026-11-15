"""Battle LOD: decimate a .fam to a triangle budget in Blender and write it back as .fam (same parts, bones, textures, colours).
usage: blender -b -P lod.py -- IN.fam OUT.fam TARGET_TRIS"""
import bpy,bmesh,sys,struct,math
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
a=sys.argv[sys.argv.index('--')+1:];src,dst,T=a[0],a[1],int(a[2])
parts=read_fam(src);KEEP=int(__import__('os').environ.get('KEEP','300'))   # sub-meshes this small are kept as they are (bolts, lights, glass panes)
def area(sb):
    P=sb['pos'];I=sb['idx'];A=0.0
    for f in range(0,len(I),3):
        a,b,c=I[f],I[f+1],I[f+2];ux,uy,uz=P[3*b]-P[3*a],P[3*b+1]-P[3*a+1],P[3*b+2]-P[3*a+2];vx,vy,vz=P[3*c]-P[3*a],P[3*c+1]-P[3*a+1],P[3*c+2]-P[3*a+2]
        A+=0.5*math.sqrt((uy*vz-uz*vy)**2+(uz*vx-ux*vz)**2+(ux*vy-uy*vx)**2)
    return A
subs=[sb for _,ss in parts for sb in ss];N=[len(sb['idx'])//3 for sb in subs];AR=[area(sb) for sb in subs];tot=sum(N)
# Even triangle density: dense parts (bolts, grilles, tyre treads) are reduced, sparse large panels are kept.
def budget(d):return sum(n if n<=KEEP else min(n,max(KEEP,d*a)) for n,a in zip(N,AR))
lo,hi=0.0,max(n/max(a,1e-9) for n,a in zip(N,AR))+1
for _ in range(60):
    mid=(lo+hi)/2
    if budget(mid)>T:hi=mid
    else:lo=mid
D=lo;RAT={id(sb):(1.0 if n<=KEEP else min(1.0,max(KEEP,D*a)/n)) for sb,n,a in zip(subs,N,AR)}
print('LOD total',tot,'density',round(D,2),'budget',round(budget(D)),flush=True)
out=[]
for bone,ss in parts:
    nsubs=[]
    for sb in ss:
        nt=len(sb['idx'])//3
        r=RAT[id(sb)]
        if nt<=KEEP or r>=0.999:nsubs.append(sb);continue
        P=sb['pos'];UV=sb['uv'];I=sb['idx'];nv=len(P)//3
        key={};vid=[];verts=[]
        for i in range(nv):   # weld split vertices (same position and UV) so the decimator sees one surface per UV island
            k=(round(P[3*i],5),round(P[3*i+1],5),round(P[3*i+2],5),round(UV[2*i],4),round(UV[2*i+1],4))   # keep UV seams: an island edge stays a mesh edge
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
        nsubs.append(dict(tex=sb['tex'],col=sb['col'],pos=pos,nrm=nrm,uv=uv,idx=idx))
        bpy.data.objects.remove(ob);bpy.data.meshes.remove(me)
    out.append((bone,nsubs))
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
