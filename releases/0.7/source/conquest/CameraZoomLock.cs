using System.Diagnostics;
using System.Runtime.InteropServices;
using MelonLoader;

namespace FreedomArrow.Conquest;
// 0.6 dev.6 (Osama, 7 November 2026): zooming in over a unit zooms normally and does not lock the camera onto the unit.
// Read from the game code (GameAssembly 6000.3.24f1): the mouse-wheel zoom (CameraScrollSystem.ScrollForward, compiled
// into the code at RVA 0x7B3A10) first calls a unit-under-cursor check (RVA 0x7B3E30) that attaches the follow camera
// and returns true; on true the normal zoom is skipped. dev.2-dev.5 blocked only the attach, so the zoom was skipped too.
// Here the call at RVA 0x7B3B19 (e8 12 03 00 00) becomes "xor eax,eax" (31 c0 90 90 90): the check reads false and the
// normal zoom runs. The bytes are compared first; on another game build nothing is written.
public sealed partial class Prototype
{
    const int ZoomCallRva=0x7B3B19;
    static readonly byte[] ZoomCallOld={0xE8,0x12,0x03,0x00,0x00},ZoomCallNew={0x31,0xC0,0x90,0x90,0x90};
    [DllImport("kernel32.dll")] static extern bool VirtualProtect(IntPtr address,UIntPtr size,uint protect,out uint old);
    static void InstallCameraZoomLock()
    {
        var module=Process.GetCurrentProcess().Modules.Cast<ProcessModule>().FirstOrDefault(m=>m.ModuleName.Equals("GameAssembly.dll",StringComparison.OrdinalIgnoreCase))
            ?? throw new InvalidOperationException("GameAssembly.dll not found");
        var at=module.BaseAddress+ZoomCallRva;
        var now=new byte[5];Marshal.Copy(at,now,0,5);
        if(now.SequenceEqual(ZoomCallNew)){MelonLogger.Msg("FREEDOM_ARROW_CAMERA_ZOOM_LOCK already patched");return;}
        if(!now.SequenceEqual(ZoomCallOld))throw new InvalidOperationException("unexpected game code at the zoom call ("+Convert.ToHexString(now)+"); camera left as vanilla");
        if(!VirtualProtect(at,(UIntPtr)5,0x40,out uint old))throw new InvalidOperationException("VirtualProtect failed");
        Marshal.Copy(ZoomCallNew,0,at,5);
        VirtualProtect(at,(UIntPtr)5,old,out _);
        Marshal.Copy(at,now,0,5);
        MelonLogger.Msg("FREEDOM_ARROW_CAMERA_ZOOM_LOCK installed: zooming in over a unit zooms normally, no follow ("+Convert.ToHexString(now)+")");
    }
}
