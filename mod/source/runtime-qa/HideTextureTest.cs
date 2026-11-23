using System.Text.Json.Nodes;
using MelonLoader;
using UnityEngine;

namespace FreedomArrow;

// Diagnostic switch for the flat brown explosion sheet (Osama 17 Nov 2026 10:4x PST, thread 1567745029781454889, from the TARS handoff
// work/reports/entries/effects-brown-sheet-20261117: "test by temporarily hiding only that texture's smoke layer ... then reproduce the PLL-09 and
// JRVG impacts. If the flat brown sheet disappears, that confirms the link"). Off unless UserData/FreedomArrow/hide-textures.json exists:
//   {"textures": ["Texture_Smoke_Brown_BaseMap"]}
// Every 3 s the file is read again and loaded Texture2D objects with a listed name are blanked on the GPU (a copy of a zero-filled texture
// of the same size, format and mip count: DXT5/BC7/BC3 zero blocks are fully transparent). The original pixels are kept in a backup texture
// and copied back when the name leaves the list or the file is deleted, so the test can be switched on and off during a match. The effects
// graphs (VFX Graph) that sample the texture are not changed. Logs FREEDOM_ARROW_HIDE_TEXTURE lines (format, size, mips, on/off).
static class HideTextureTest
{
    static string file="";static float next;static DateTime stamp;static HashSet<string> names=new();
    sealed class Hidden{public Texture2D Tex=null!;public Texture2D Backup=null!;}
    static readonly Dictionary<int,Hidden> hidden=new();
    static int logs;
    public static void Install(string root){file=Path.Combine(root,"hide-textures.json");}
    public static void LateUpdate()
    {
        if(file.Length==0)return;
        float now=Time.unscaledTime;if(now<next)return;next=now+3f;
        try
        {
            ReadConfig();
            // Put back anything no longer listed (or whose texture was unloaded).
            foreach(var id in hidden.Keys.ToList())
            {
                var h=hidden[id];
                if(h.Tex==null){hidden.Remove(id);continue;}
                if(names.Contains(h.Tex.name))continue;
                Graphics.CopyTexture(h.Backup,h.Tex);UnityEngine.Object.Destroy(h.Backup);hidden.Remove(id);
                Log($"restored {h.Tex.name}");
            }
            if(names.Count==0)return;
            foreach(var t in Resources.FindObjectsOfTypeAll<Texture2D>())
            {
                if(t==null||!names.Contains(t.name))continue;
                int id=t.GetInstanceID();if(hidden.ContainsKey(id))continue;
                hidden[id]=Blank(t);
            }
        }
        catch(Exception x){if(logs++<20)MelonLogger.Warning("FREEDOM_ARROW_HIDE_TEXTURE failed: "+x.Message);}
    }
    static void ReadConfig()
    {
        if(!File.Exists(file)){if(names.Count>0){names=new();Log("switch file removed: restoring");}stamp=default;return;}
        var t=File.GetLastWriteTimeUtc(file);if(t==stamp)return;stamp=t;
        names=(JsonNode.Parse(File.ReadAllText(file))?["textures"]?.AsArray().Select(x=>(string)x!).ToHashSet())??new();
        Log($"switch on for: {string.Join(", ",names)}");
    }
    static Hidden Blank(Texture2D t)
    {
        int mips=t.mipmapCount;var fmt=t.format;
        // Crunched textures sit on the GPU as plain DXT1/DXT5.
        if(fmt==TextureFormat.DXT5Crunched)fmt=TextureFormat.DXT5;else if(fmt==TextureFormat.DXT1Crunched)fmt=TextureFormat.DXT1;
        var backup=new Texture2D(t.width,t.height,fmt,mips,false){name=t.name+" (FA backup)"};
        Graphics.CopyTexture(t,backup);
        var blank=new Texture2D(t.width,t.height,fmt,mips,false);
        var raw=new byte[RawSize(t.width,t.height,mips,fmt)];
        // DXT1 zero blocks are opaque black; colour index 3 with color0 <= color1 is transparent.
        if(fmt==TextureFormat.DXT1)for(int i=4;i<raw.Length;i+=8){raw[i]=raw[i+1]=raw[i+2]=raw[i+3]=0xFF;}
        blank.LoadRawTextureData(raw);blank.Apply(false,false);
        Graphics.CopyTexture(blank,t);UnityEngine.Object.Destroy(blank);
        Log($"hid {t.name}: {t.width}x{t.height} {t.format} mips {mips}");
        return new Hidden{Tex=t,Backup=backup};
    }
    // Block-compressed size of all mips: 4x4 blocks, 8 bytes (DXT1/BC4) or 16 bytes (DXT5/BC5/BC7); RGBA32 4 bytes per pixel.
    static int RawSize(int w,int h,int mips,TextureFormat f)
    {
        int bpb=f switch{TextureFormat.DXT1=>8,TextureFormat.BC4=>8,TextureFormat.DXT5=>16,TextureFormat.BC5=>16,TextureFormat.BC7=>16,TextureFormat.BC6H=>16,_=>0};
        int n=0;
        for(int m=0;m<mips;m++)
        {
            int mw=Math.Max(1,w>>m),mh=Math.Max(1,h>>m);
            n+=bpb>0?((mw+3)/4)*((mh+3)/4)*bpb:mw*mh*(f==TextureFormat.RGBA32||f==TextureFormat.ARGB32?4:throw new NotSupportedException("format "+f));
        }
        return n;
    }
    static void Log(string s){if(logs++<200)MelonLogger.Msg("FREEDOM_ARROW_HIDE_TEXTURE "+s);}
}
