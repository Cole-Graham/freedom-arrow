using System.Diagnostics;
using System.Runtime.InteropServices;
using MelonLoader;

namespace FreedomArrow.Conquest;
// Pinned native call sites, not native-to-managed detours. ScrollForward checks the cursor target first;
// Update then checks it again and skips its altitude zoom when that second check succeeds. Both must
// return false for wheel input to pass through unit labels. Other camera controls and UI gates remain native.
public sealed partial class Prototype
{
    internal static readonly int[] ZoomCallRvas={0x7B3B19,0x7C0FCB};
    internal static readonly byte[][] ZoomCallsOld={new byte[]{0xE8,0x12,0x03,0x00,0x00},new byte[]{0xE8,0x70,0x31,0xFF,0xFF}};
    internal static readonly byte[][] ZoomTails={new byte[]{0x84,0xC0,0x0F,0x85,0xAD,0x02,0x00,0x00},new byte[]{0x84,0xC0,0x0F,0x85,0x88,0x00,0x00,0x00}};
    internal static readonly byte[] ZoomCallNew={0x31,0xC0,0x90,0x90,0x90};
    [DllImport("kernel32.dll")] static extern bool VirtualProtect(IntPtr address,UIntPtr size,uint protect,out uint old);
    [DllImport("kernel32.dll")] static extern bool FlushInstructionCache(IntPtr process,IntPtr address,UIntPtr size);

    // Validate the complete pair before any write. Accept our earlier one-site patch and repeat installs.
    internal static bool[] PlanCameraZoom(byte[][] current)
    {
        if(current.Length!=ZoomCallRvas.Length)throw new ArgumentException("expected both camera call sites");
        var change=new bool[current.Length];
        for(int i=0;i<current.Length;i++)
        {
            var bytes=current[i];
            if(bytes.Length!=13||!bytes.Skip(5).SequenceEqual(ZoomTails[i])||
                (!bytes.Take(5).SequenceEqual(ZoomCallsOld[i])&&!bytes.Take(5).SequenceEqual(ZoomCallNew)))
                throw new InvalidOperationException($"unexpected camera code at RVA {ZoomCallRvas[i]:X}; camera patch aborted before writes");
            change[i]=!bytes.Take(5).SequenceEqual(ZoomCallNew);
        }
        return change;
    }
    static void WriteCameraZoom(IntPtr at,byte[] bytes)
    {
        if(!VirtualProtect(at,(UIntPtr)5,0x40,out uint old))throw new InvalidOperationException("camera VirtualProtect failed");
        try
        {
            Marshal.Copy(bytes,0,at,5);
            if(!FlushInstructionCache(Process.GetCurrentProcess().Handle,at,(UIntPtr)5))throw new InvalidOperationException("camera instruction-cache flush failed");
        }
        finally
        {
            if(!VirtualProtect(at,(UIntPtr)5,old,out _))throw new InvalidOperationException("camera protection restore failed");
        }
    }
    static void InstallCameraZoomLock()
    {
        var module=Process.GetCurrentProcess().Modules.Cast<ProcessModule>().FirstOrDefault(m=>m.ModuleName.Equals("GameAssembly.dll",StringComparison.OrdinalIgnoreCase))
            ?? throw new InvalidOperationException("GameAssembly.dll not found");
        var previous=ZoomCallRvas.Select(rva=>{var b=new byte[13];Marshal.Copy(module.BaseAddress+rva,b,0,b.Length);return b;}).ToArray();
        var change=PlanCameraZoom(previous);var touched=new List<int>();
        try
        {
            for(int i=0;i<change.Length;i++)if(change[i])
            {
                touched.Add(i);WriteCameraZoom(module.BaseAddress+ZoomCallRvas[i],ZoomCallNew);
            }
            var after=ZoomCallRvas.Select(rva=>{var b=new byte[13];Marshal.Copy(module.BaseAddress+rva,b,0,b.Length);return b;}).ToArray();
            if(PlanCameraZoom(after).Any(x=>x))throw new InvalidOperationException("camera patch readback failed");
        }
        catch
        {
            foreach(int i in touched.AsEnumerable().Reverse())
            {
                try{WriteCameraZoom(module.BaseAddress+ZoomCallRvas[i],previous[i].Take(5).ToArray());}
                catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_CAMERA_ROLLBACK_FAILED: "+e.Message);}
            }
            throw;
        }
        MelonLogger.Msg("FREEDOM_ARROW_CAMERA_ZOOM_LOCK installed: both wheel follow checks bypassed; unit labels no longer consume zoom; native UI gates retained (2/2 sites verified)");
    }
}
