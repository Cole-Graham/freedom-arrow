using System.Collections.Concurrent;
namespace FAModels;
// 0.3.31 (Osama 15 Nov: "we should apply all of these techniques that vanilla does to optimize their performance"). Vanilla's
// meshes and textures come ready-made from its bundles and Unity reads them on background threads. Ours did all the work on the
// game's main thread: read the .fam file, convert its arrays, calculate tangents (RecalculateTangents), read each .fat texture.
// Now everything that is plain data runs on background CPU cores as soon as the decks are known (Prefetch): the file read, the
// array conversion, the tangents and the bounds, and the texture bytes. The main thread only creates the Mesh and Texture objects
// (Unity allows that only on the main thread) and uploads the ready arrays. The background code uses no Unity type or call at all
// (not even Vector3 or Color): those are IL2CPP objects and must not be touched from another thread. A spawn before the prefetch finishes waits for it,
// which is still faster than doing it all itself.
public partial class Mod
{
    sealed class FamSubData { public string tex = ""; public float[] col = new float[4]; public float[] pos = Array.Empty<float>(), nrm = Array.Empty<float>(), uv = Array.Empty<float>(), tan = Array.Empty<float>(); public int[] idx = Array.Empty<int>(); public bool anyN; public float[] min = new float[3], max = new float[3]; }
    sealed class FamPartData { public string bone = ""; public List<FamSubData> subs = new(); }
    sealed class FatData { public int w, h, fmt, mips; public bool lin; public byte[] data = Array.Empty<byte>(); }
    static readonly ConcurrentDictionary<string, Task<List<FamPartData>>> famJobs = new();
    static readonly ConcurrentDictionary<string, FatData> fatReady = new();
    // 0.3.47: .fat files already on the GPU (Tex). A heavier level shares the lightest level's textures; its background read re-read them
    // into fatReady, where nothing took them again, so each such read held a model's texture bytes in RAM for the rest of the session.
    static readonly ConcurrentDictionary<string, byte> texMade = new();

    // Start reading and preparing a model (and its textures) on a background thread. Safe to call more than once.
    static void Prefetch(string file)
    {
        if (string.IsNullOrEmpty(file) || famCache.ContainsKey(file)) return;
        if (!famJobs.ContainsKey(file)) famJobs.TryAdd(file, Task.Run(new Func<List<FamPartData>>(new PrepareJob(file).Run)));
    }
    sealed class PrepareJob
    {
        readonly string file; public PrepareJob(string f) { file = f; }
        public List<FamPartData> Run() { var d = ParseFamData(file); foreach (var p in d) foreach (var s in p.subs) PrefetchTextures(s.tex); return d; }
    }
    static bool FamReady(string file) => famCache.ContainsKey(file) || (famJobs.TryGetValue(file, out var t) && t.IsCompleted);

    static List<FamPartData> ParseFamData(string file)
    {
        var parts = new List<FamPartData>();
        using var f = new BinaryReader(File.OpenRead(Path.Combine(dir, file)));
        if (new string(f.ReadChars(4)) != "FAM1") throw new Exception("not a FAM1 file");
        int np = f.ReadInt32();
        for (int p = 0; p < np; p++)
        {
            var part = new FamPartData { bone = Str(f) }; int ns = f.ReadInt32();
            // 0.3.31: sub-meshes of one part with the same texture and colour are merged into one, so they need one renderer (one draw
            // call) instead of many. Some converted models had hundreds per vehicle (CSK-181 1,135, PHL-16 601, ZBD-05 472); merged, the
            // 191 battle models go from 8,678 renderers to 918. The material is chosen by texture and colour, so nothing looks different.
            var byKey = new Dictionary<string, List<FamSubData>>(); var order = new List<string>();
            for (int s = 0; s < ns; s++)
            {
                var d = new FamSubData { tex = Str(f), col = new[] { f.ReadSingle(), f.ReadSingle(), f.ReadSingle(), f.ReadSingle() } };
                int nv = f.ReadInt32();
                d.pos = Floats(f, nv * 3); d.nrm = Floats(f, nv * 3); d.uv = Floats(f, nv * 2);
                int ni = f.ReadInt32(); var bi = f.ReadBytes(ni * 4); d.idx = new int[ni]; Buffer.BlockCopy(bi, 0, d.idx, 0, bi.Length);
                string key = d.tex + "|" + string.Join(",", d.col.Select(x => BitConverter.SingleToInt32Bits(x)));
                if (!byKey.TryGetValue(key, out var list)) { byKey[key] = list = new List<FamSubData>(); order.Add(key); }
                list.Add(d);
            }
            foreach (var key in order)
            {
                var list = byKey[key]; var d = list.Count == 1 ? list[0] : Merge(list);
                int nv = d.pos.Length / 3;
                for (int k = 0; k < d.nrm.Length && !d.anyN; k++) d.anyN = d.nrm[k] != 0;
                for (int j = 0; j < 3; j++) { d.min[j] = float.MaxValue; d.max[j] = float.MinValue; }
                for (int k = 0; k < nv; k++) for (int j = 0; j < 3; j++) { float v = d.pos[3 * k + j]; if (v < d.min[j]) d.min[j] = v; if (v > d.max[j]) d.max[j] = v; }
                if (d.anyN) d.tan = Tangents(d.pos, d.nrm, d.uv, d.idx);
                part.subs.Add(d);
            }
            parts.Add(part);
        }
        return parts;
    }

    static FamSubData Merge(List<FamSubData> list)
    {
        var d = new FamSubData { tex = list[0].tex, col = list[0].col };
        int nv = list.Sum(x => x.pos.Length / 3), ni = list.Sum(x => x.idx.Length);
        d.pos = new float[nv * 3]; d.nrm = new float[nv * 3]; d.uv = new float[nv * 2]; d.idx = new int[ni];
        int v0 = 0, i0 = 0;
        foreach (var x in list)
        {
            int n = x.pos.Length / 3;
            Array.Copy(x.pos, 0, d.pos, v0 * 3, n * 3); Array.Copy(x.nrm, 0, d.nrm, v0 * 3, n * 3); Array.Copy(x.uv, 0, d.uv, v0 * 2, n * 2);
            for (int k = 0; k < x.idx.Length; k++) d.idx[i0 + k] = x.idx[k] + v0;
            v0 += n; i0 += x.idx.Length;
        }
        return d;
    }
    // Per-vertex tangents from the triangles' UV directions (Lengyel's method, the same result shape as Mesh.RecalculateTangents):
    // xyz along +U, w = handedness so that binormal = cross(normal, tangent) * w.
    static float[] Tangents(float[] p, float[] n, float[] uv, int[] idx)
    {
        int nv = p.Length / 3; var t1 = new float[nv * 3]; var t2 = new float[nv * 3]; var r = new float[nv * 4];
        for (int i = 0; i + 2 < idx.Length; i += 3)
        {
            int a = idx[i], b = idx[i + 1], c = idx[i + 2];
            float x1 = p[3 * b] - p[3 * a], y1 = p[3 * b + 1] - p[3 * a + 1], z1 = p[3 * b + 2] - p[3 * a + 2];
            float x2 = p[3 * c] - p[3 * a], y2 = p[3 * c + 1] - p[3 * a + 1], z2 = p[3 * c + 2] - p[3 * a + 2];
            float s1 = uv[2 * b] - uv[2 * a], u1 = uv[2 * b + 1] - uv[2 * a + 1], s2 = uv[2 * c] - uv[2 * a], u2 = uv[2 * c + 1] - uv[2 * a + 1];
            float den = s1 * u2 - s2 * u1; if (Math.Abs(den) < 1e-12f) continue; float q = 1f / den;
            float sx = (u2 * x1 - u1 * x2) * q, sy = (u2 * y1 - u1 * y2) * q, sz = (u2 * z1 - u1 * z2) * q;
            float tx = (s1 * x2 - s2 * x1) * q, ty = (s1 * y2 - s2 * y1) * q, tz = (s1 * z2 - s2 * z1) * q;
            foreach (int v in new[] { a, b, c }) { t1[3 * v] += sx; t1[3 * v + 1] += sy; t1[3 * v + 2] += sz; t2[3 * v] += tx; t2[3 * v + 1] += ty; t2[3 * v + 2] += tz; }
        }
        for (int v = 0; v < nv; v++)
        {
            float nx = n[3 * v], ny = n[3 * v + 1], nz = n[3 * v + 2], tx = t1[3 * v], ty = t1[3 * v + 1], tz = t1[3 * v + 2];
            float d = nx * tx + ny * ty + nz * tz; tx -= nx * d; ty -= ny * d; tz -= nz * d;
            float l = MathF.Sqrt(tx * tx + ty * ty + tz * tz);
            if (l < 1e-8f) { // no usable UV direction: any vector at right angles to the normal
                if (Math.Abs(nx) < 0.9f) { tx = 0; ty = -nz; tz = ny; } else { tx = nz; ty = 0; tz = -nx; }
                l = MathF.Sqrt(tx * tx + ty * ty + tz * tz); if (l < 1e-8f) { tx = 1; ty = tz = 0; l = 1; }
            }
            tx /= l; ty /= l; tz /= l;
            float cx = ny * tz - nz * ty, cy = nz * tx - nx * tz, cz = nx * ty - ny * tx;
            r[4 * v] = tx; r[4 * v + 1] = ty; r[4 * v + 2] = tz; r[4 * v + 3] = cx * t2[3 * v] + cy * t2[3 * v + 1] + cz * t2[3 * v + 2] < 0 ? -1f : 1f;
        }
        return r;
    }

    // Texture bytes for X.png, X_n.png and X_mask.png (as .fat), read on the background thread; Tex() takes them once.
    static void PrefetchTextures(string tex)
    {
        if (string.IsNullOrEmpty(tex)) return;
        var stem = Path.ChangeExtension(tex, null);
        foreach (var name in new[] { stem + ".fat", stem + "_n.fat", stem + "_mask.fat" })
        {
            var path = Path.Combine(dir, name);
            if (fatReady.ContainsKey(path) || texMade.ContainsKey(path) || !File.Exists(path)) continue;
            try
            {
                using var r = new BinaryReader(File.OpenRead(path));
                if (new string(r.ReadChars(4)) != "FAT1") continue;
                var d = new FatData { w = r.ReadInt32(), h = r.ReadInt32(), fmt = r.ReadInt32(), mips = r.ReadInt32(), lin = r.ReadInt32() != 0 };
                int n = r.ReadInt32(); d.data = r.ReadBytes(n); if (d.data.Length == n) fatReady.TryAdd(path, d);
            }
            catch { } // Tex() reads the file itself
        }
    }
}
