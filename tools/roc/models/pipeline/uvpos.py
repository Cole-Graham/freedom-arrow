"""CPU rasterizer (no render): world position and face normal of every texel, per material, from a GLB's UVs. Used to lay camouflage out in 3D
(Hsiung Feng IIE Woodland scheme, 26 Nov). blender -b -P uvpos.py -- IN.glb OUTDIR SIZE  -> OUTDIR/pos_<material>.npy (H,W,6 float16: xyz, normal)
Rows are bottom-up (Blender image order); unfilled texels are NaN, then grown 6 px so UV-island edges have values."""
import bpy,sys,os,numpy as np
a=sys.argv[sys.argv.index('--')+1:];glb,out,N=a[0],a[1],int(a[2]);os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
buf={}
import re
SKIP=os.environ.get('SKIP','^$')   # objects to leave out (interior, rotors, gear ...): their texels stay empty
for o in [o for o in bpy.data.objects if o.type=='MESH' and not re.search(SKIP,o.name)]:
    me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;M=o.matrix_world;R=M.to_3x3().inverted().transposed()
    P=np.array([tuple(M@v.co) for v in me.vertices]);
    for t in me.loop_triangles:
        mat=me.materials[t.material_index];
        if not mat:continue
        g=buf.setdefault(mat.name.split('.')[0],np.full((N,N,6),np.nan,np.float32))
        U=np.array([uv[l].uv[:] for l in t.loops])*N-0.5;V=P[list(t.vertices)];n=np.array(R@t.normal);n/=np.linalg.norm(n)+1e-9
        x0,y0=np.floor(U.min(0)).astype(int);x1,y1=np.ceil(U.max(0)).astype(int)
        xs=np.arange(x0,x1+1);ys=np.arange(y0,y1+1);X,Y=np.meshgrid(xs,ys)
        (ax,ay),(bx,by),(cx,cy)=U;d=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(d)<1e-12:continue
        l1=((by-cy)*(X-cx)+(cx-bx)*(Y-cy))/d;l2=((cy-ay)*(X-cx)+(ax-cx)*(Y-cy))/d;l3=1-l1-l2;ins=(l1>=-0.02)&(l2>=-0.02)&(l3>=-0.02)
        if not ins.any():continue
        Xi=X[ins]%N;Yi=Y[ins]%N;pos=l1[ins,None]*V[0]+l2[ins,None]*V[1]+l3[ins,None]*V[2]
        g[Yi,Xi,:3]=pos;g[Yi,Xi,3:]=n
for m,g in buf.items():
    for it in range(6):   # grow into empty texels from 4 neighbours
        e=np.isnan(g[...,0])
        if not e.any():break
        for sh in ((1,0),(-1,0),(0,1),(0,-1)):
            s=np.roll(g,sh,axis=(0,1));f=e&~np.isnan(s[...,0]);g[f]=s[f];e=np.isnan(g[...,0])
    np.save(f'{out}/pos_{m}.npy',g.astype(np.float16));print('UVPOS',m,'filled %.2f'%(1-np.isnan(g[...,0]).mean()))
