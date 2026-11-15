"""Cut an FAS1 infantry body to a triangle budget, keeping its skin weights. usage: blender -b -P decimate_fas.py -- IN.fas OUT.fas TARGET_TRIS
Per material: weld the GPU seam copies, Decimate (collapse) at one ratio for the whole body, copy the original normals back
(nearest-face interpolated), split by UV/normal again and keep the 4 strongest weights per vertex, normalised. Only bones that
already carry weight in IN can carry weight in OUT (checked), so the native lower LODs' missing finger bones stay unweighted."""
import bpy, bmesh, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fas
a = sys.argv[sys.argv.index('--') + 1:]; src, dst, target = a[0], a[1], int(a[2])
bones, subs = fas.read(src); before = fas.tris(subs); ratio = min(1.0, target / before)
bpy.ops.wm.read_factory_settings(use_empty=True)
col = bpy.context.collection; out = []


def build(sub, name):
    V = [v[0] for v in sub['verts']]; I = sub['idx']
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], [tuple(I[j:j + 3]) for j in range(0, len(I), 3)]); me.update()
    uv = me.uv_layers.new()
    for li, l in enumerate(me.loops): uv.data[li].uv = sub['verts'][l.vertex_index][2]
    me.normals_split_custom_set([sub['verts'][l.vertex_index][1] for l in me.loops])
    ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    groups = [ob.vertex_groups.new(name=str(i)) for i in range(40)]
    for vi, (_, _, _, bi, bw) in enumerate(sub['verts']):
        for b, w in zip(bi, bw):
            if w > 0: groups[b].add([vi], w, 'ADD')
    return ob


for k, sub in enumerate(subs):
    ref = build(sub, f'ref{k}'); ob = build(sub, f'cut{k}')
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.objects.active = ob
    if ratio < 1:
        d = ob.modifiers.new('cut', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = ratio; d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='cut')
    t = ob.modifiers.new('nrm', 'DATA_TRANSFER'); t.object = ref; t.use_loop_data = True; t.data_types_loops = {'CUSTOM_NORMAL'}; t.loop_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier='nrm')
    me = ob.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data; cn = me.corner_normals
    gi = {g.index: int(g.name) for g in ob.vertex_groups}
    keymap = {}; verts = []; idx = []
    for tri in me.loop_triangles:
        for li in tri.loops:
            vi = me.loops[li].vertex_index; u = tuple(uv[li].uv); n = tuple(cn[li].vector)
            key = (vi, round(u[0], 6), round(u[1], 6), round(n[0], 4), round(n[1], 4), round(n[2], 4))
            if key not in keymap:
                ws = sorted(((gi[g.group], g.weight) for g in me.vertices[vi].groups if g.weight > 0), key=lambda x: -x[1])[:4]
                assert ws, f'unweighted vertex {vi}'
                s = sum(w for _, w in ws); ws = [(b, w / s) for b, w in ws] + [(0, 0.0)] * (4 - len(ws))
                keymap[key] = len(verts); verts.append((tuple(me.vertices[vi].co), n, u, tuple(b for b, _ in ws), tuple(w for _, w in ws)))
            idx.append(keymap[key])
    out.append({'tex': sub['tex'], 'verts': verts, 'idx': idx})
fas.check(bones, out)
assert fas.weighted_bones(out) <= fas.weighted_bones(subs), 'new weighted bone'
fas.write(dst, bones, out)
print(f'FASCUT {os.path.basename(src)} {before} -> {fas.tris(out)} tris (target {target}), verts {sum(len(s["verts"]) for s in subs)} -> {sum(len(s["verts"]) for s in out)}')
