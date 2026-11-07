using HarmonyLib;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.Camera;
using Il2CppBrokenArrow.Client.Ecs.Camera.Systems;

namespace FreedomArrow.Conquest;
// 0.6 dev.2 (Osama, 7 November 2026): zooming in no longer locks the camera onto a unit.
// Read from the game code: the mouse-wheel system (CameraScrollSystem.Update) picks the unit under the cursor while
// zooming in and calls CameraService.AttachToUnit(in Entity, in Entity), which starts the follow camera.
// While that system runs, AttachToUnit is skipped. Other callers (double-click follow, aircraft view) are unchanged.
public sealed partial class Prototype
{
    [ThreadStatic] static bool inCameraScroll;
    static int zoomLocksBlocked;
    static void InstallCameraZoomLock()
    {
        Patch(typeof(CameraScrollSystem),"Update",nameof(CameraScrollBefore),nameof(CameraScrollAfter));
        var attach=AccessTools.GetDeclaredMethods(typeof(CameraService)).Single(m=>m.Name=="AttachToUnit"&&m.IsStatic&&m.GetParameters().Length==2);
        instance!.HarmonyInstance.Patch(attach,prefix:new HarmonyMethod(typeof(Prototype),nameof(CameraAttachBefore)));
        MelonLogger.Msg("FREEDOM_ARROW_CAMERA_ZOOM_LOCK installed: zooming in does not follow a unit");
    }
    public static void CameraScrollBefore()=>inCameraScroll=true;
    public static void CameraScrollAfter()=>inCameraScroll=false;
    public static bool CameraAttachBefore()
    {
        if(!inCameraScroll)return true;
        if(++zoomLocksBlocked<=5)MelonLogger.Msg($"FREEDOM_ARROW_CAMERA_ZOOM_LOCK blocked a zoom-in follow ({zoomLocksBlocked})");
        return false;
    }
}
