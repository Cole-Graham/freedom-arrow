import bpy,sys,math
args=sys.argv[sys.argv.index('--')+1:];obj,mat,res=args[0],args[1],int(args[2])
o=bpy.data.objects[obj];me=o.data;M=o.matrix_world;uv=me.uv_layers.active.data
A3=Auv=0
for p in me.polygons:
    if me.materials[p.material_index].name!=mat:continue
    vs=[M@me.vertices[i].co for i in p.vertices];us=[uv[l].uv for l in p.loop_indices]
    for k in range(1,len(vs)-1):
        A3+=((vs[k]-vs[0]).cross(vs[k+1]-vs[0])).length/2
        a=us[k]-us[0];b=us[k+1]-us[0];Auv+=abs(a.x*b.y-a.y*b.x)/2
print('TEXEL',obj,mat,round(A3,4),'m2',round(Auv,4),'uv',round(math.sqrt(Auv*res*res/A3)),'px/m')
