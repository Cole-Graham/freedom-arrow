"""uv_zmask.py: UV polygons (JSON) of faces lying entirely below ZMAX (boots), for one material."""
import bpy,sys,json
out,mat,zmax=sys.argv[sys.argv.index('--')+1:];zmax=float(zmax)
o=next(o for o in bpy.data.objects if o.type=='MESH');me=o.data;uv=me.uv_layers.active.data;M=o.matrix_world
polys=[[(uv[l].uv.x,1-uv[l].uv.y) for l in p.loop_indices] for p in me.polygons if me.materials[p.material_index].name==mat and max((M@me.vertices[i].co).z for i in p.vertices)<zmax]
json.dump(polys,open(out,'w'));print('ZMASK faces',len(polys))
