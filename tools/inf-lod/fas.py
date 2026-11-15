"""Read and write FAS1 skinned infantry bodies (format: InfantryBodies.ParseBody in FAModels).
FAS1, int32 bone count (40), bone names, int32 sub count; per sub: texture name, int32 nv, nv x (pos3, nrm3, uv2 float32, bone idx int32 x4,
weight float32 x4), int32 ni, ni int32 indices."""
import struct


def read(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'FAS1', path
    o = 4

    def i32():
        nonlocal o
        v = struct.unpack_from('<i', b, o)[0]; o += 4; return v

    def s():
        nonlocal o
        n = i32(); r = b[o:o + n].decode(); o += n; return r
    bones = [s() for _ in range(i32())]
    subs = []
    for _ in range(i32()):
        tex = s(); nv = i32(); verts = []
        for _ in range(nv):
            f = struct.unpack_from('<8f4i4f', b, o); o += 64
            verts.append((f[0:3], f[3:6], f[6:8], f[8:12], f[12:16]))
        ni = i32(); idx = list(struct.unpack_from('<%di' % ni, b, o)); o += 4 * ni
        subs.append({'tex': tex, 'verts': verts, 'idx': idx})
    assert o == len(b), 'trailing data ' + path
    return bones, subs


def write(path, bones, subs):
    out = [b'FAS1', struct.pack('<i', len(bones))]

    def s(t):
        e = t.encode(); out.append(struct.pack('<i', len(e)) + e)
    for n in bones: s(n)
    out.append(struct.pack('<i', len(subs)))
    for sub in subs:
        s(sub['tex']); out.append(struct.pack('<i', len(sub['verts'])))
        for p, n, uv, bi, bw in sub['verts']:
            out.append(struct.pack('<8f4i4f', *p, *n, *uv, *bi, *bw))
        out.append(struct.pack('<i', len(sub['idx'])) + struct.pack('<%di' % len(sub['idx']), *sub['idx']))
    open(path, 'wb').write(b''.join(out))


def tris(subs):
    return sum(len(s['idx']) // 3 for s in subs)


def check(bones, subs):
    """The loader's own limits (ParseBody): 40 bones, 1-8 subs, nv <= 200000, weights sum to 1 within 0.001, indices in range."""
    assert len(bones) == 40 and 1 <= len(subs) <= 8
    for s in subs:
        nv = len(s['verts']); assert 1 <= nv <= 200000 and 3 <= len(s['idx']) <= 600000 and len(s['idx']) % 3 == 0
        assert all(0 <= i < nv for i in s['idx'])
        for p, n, uv, bi, bw in s['verts']:
            assert all(0 <= x < 40 for x in bi) and all(w >= 0 for w in bw) and abs(sum(bw) - 1) <= 0.001


def weighted_bones(subs):
    return {bi for s in subs for _, _, _, b4, w4 in s['verts'] for bi, w in zip(b4, w4) if w > 0}
