using System.Collections.Concurrent;
using System.Text.Json;
using MelonLoader;
using MelonLoader.Utils;
using Il2CppDefaultEcs;
using Il2CppBrokenArrow.Core.Security;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppBrokenArrow.Shared.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Shared.Ecs.Components;

namespace FreedomArrow.Conquest;
// 0.5 dev.35 (Lateralus): infantry disposable launchers fire at 12.16 x carriers^(1/3) per minute per squad.
// Soldiers carrying the same launcher share one weapon and each reloads on his own (squad rate = 60 x carriers / reload),
// so each squad's weapon gets reload = 60 x carriers / rate. The per-squad values come from squad-reload.json (build time).
// On the first shot of a squad's launcher the reload is written and the weapon is remembered; each later reload roll of
// that weapon is overwritten with the same value (GenerateRandomMagazineReloadTime and SetRandomParams). The unit card's rate of fire uses the same formula.
public sealed partial class Prototype
{
    static Dictionary<string,float> squadReload;
    static float rofK,rofExp;static int rofType=-1;
    static readonly ConcurrentDictionary<IntPtr,float> reloadByWeapon=new();
    static int squadReloadLogged;
    static void InstallSquadReload()
    {
        var path=Path.Combine(MelonEnvironment.GameRootDirectory,"UserData","FreedomArrow","squad-reload.json");
        using var doc=JsonDocument.Parse(File.ReadAllText(path));var root=doc.RootElement;
        rofK=root.GetProperty("k").GetSingle();rofExp=root.GetProperty("exponent").GetSingle();rofType=root.GetProperty("disposableType").GetInt32();
        squadReload=new();
        foreach(var p in root.GetProperty("squads").EnumerateObject())squadReload[p.Name]=p.Value.GetProperty("reload").GetSingle();
        Patch(typeof(WeaponComponent),"GenerateRandomMagazineReloadTime",null,nameof(SquadReloadRolled));
        // dev.36: SetRandomParams rolls aim, burst and reload itself (inlined) and writes the reload field directly.
        Patch(typeof(WeaponComponent),"SetRandomParams",null,nameof(SquadReloadRolled));
        Patch(typeof(WeaponHelper),"RateOfFire",null,nameof(SquadCardRate));
        MelonLogger.Msg($"FREEDOM_ARROW_SQUAD_RELOAD installed: {squadReload.Count} squad launchers, rate {rofK} x carriers^{rofExp:0.###}");
    }
    // Called from CountShot after a real shot, when the weapon and its unit are fully set up.
    static void SquadReloadShot(WeaponComponent w)
    {
        if(squadReload==null||w.WeaponInfo==null||(int)w.WeaponInfo.Type!=rofType)return;
        // dev.37: the game puts the data reload back after each reload by a path neither hook below sees
        // (dev.36 editor test: first gap 2.89 s, then 1.41 s again), so a registered weapon is rewritten on every shot.
        if(reloadByWeapon.TryGetValue(w.Pointer,out float known)){w._magazineReloadTime=new GFloat(known);return;}
        var unit=w.GetUnitEntity();
        if(!unit.IsAlive||!unit.Has<UnitComponent>())return;
        int uid=NativeEcs.Read<UnitComponent>(unit).UnitData?.Id??0;
        if(!squadReload.TryGetValue($"{uid}:{w.WeaponInfo.Id}",out float reload))return;
        reloadByWeapon[w.Pointer]=reload;
        w._magazineReloadTime=new GFloat(reload);
        if(++squadReloadLogged<=50)MelonLogger.Msg($"FREEDOM_ARROW_SQUAD_RELOAD unit {uid} weapon {w.WeaponInfo.Id} reload {reload:0.##} s");
        ShotLine("squad_reload",new{unit=uid,weaponId=w.WeaponInfo.Id,reload});
    }
    // Only weapons already registered by a shot are touched; nothing else is read here.
    public static void SquadReloadRolled(WeaponComponent __instance)
    {
        if(reloadByWeapon.TryGetValue(__instance.Pointer,out float reload))__instance._magazineReloadTime=new GFloat(reload);
    }
    // The card may ask for one launcher's rate and multiply by the carrier count itself. Then the carrier count is
    // only known in the rounding call, so the per-launcher rate is remembered and the rounding hook converts.
    [ThreadStatic] static float cardPerLauncher;
    public static void SquadCardRate(Weapons weapon,int countOfWeapon,ref float __result)
    {
        cardPerLauncher=0;
        if(rofType<0||weapon==null||CardType(weapon)!=rofType||weapon.MagazineSize!=1||countOfWeapon<1)return;
        if(countOfWeapon>1){__result=rofK*MathF.Pow(countOfWeapon,rofExp);return;}
        cardPerLauncher=__result;
    }
    static float SquadCardValue(float shown)
    {
        float per=cardPerLauncher;cardPerLauncher=0;
        if(per<=0)return shown;
        int n=(int)MathF.Round(shown/per);
        return n>=1&&MathF.Abs(shown-per*n)<0.01f*shown?rofK*MathF.Pow(n,rofExp):shown;
    }
}
