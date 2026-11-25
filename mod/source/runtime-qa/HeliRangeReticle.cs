using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;
using Il2CppBrokenArrow.Client.Ecs.UI.TargetLine;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppDefaultEcs;
using Il2CppInterop.Runtime;
using MelonLoader;

namespace FreedomArrow;

// Targeting reticle range (Lateralus 25 Nov 2026 08:1x, thread 1568104480459722894: "the targeting reticle still tells the player that the MML Stinger
// is in range ... the UI targeting reticle does not reflect the 1.25 helicopter multiplier, its reflecting the ... low altitude multiplier").
// The rangefinder on the enemy under the cursor (TargetLineSystem, 1.2.2.1) does not call GetAmmoShootingDistance: RefreshLocalTargetInfo (0x4A6000)
// computes each round's max range inline as the target level's range (ammo +0xB0 ground / +0xB4 low / +0xB8 high) x the shooter's radar modifier
// (RadarAbilityComponent +0x14 / +0x18), and marks it out of range when the distance is greater (0x4A6D89-0x4A6E05). So it never saw the helicopter
// range or the per-weapon radar exemption. This postfix recomputes each round's max range with GetAmmoShootingDistance (which runs HeliRange.RangeAfter)
// and resets the out-of-range flag the same way. Layout (dump, 1.2.2.1): system +0xA4 distance, +0xA8 List<FastList<LocalAmmoInfo>>, +0xB8
// WeaponDataEntry[] (0x18 each, WeaponComponent at +0), +0xC0 weapon count; LocalAmmoInfo 0x28 each: +1 IsOutOfRange, +8 weapon name, +0x10 round
// name, +0x24 MaxRange; WeaponComponent +0x88 (int id, bool)[] rounds.
internal static class HeliRangeReticle
{
    static bool broken;static int logs;
    static readonly Dictionary<string,Ammunitions> rounds=new();
    public static void Install(HarmonyLib.Harmony h)
    {
        try
        {
            h.Patch(AccessTools.Method(typeof(TargetLineSystem),"RefreshLocalTargetInfo"),postfix:new HarmonyMethod(typeof(HeliRangeReticle),nameof(After)));
            MelonLogger.Msg("FREEDOM_ARROW_RETICLE installed: rangefinder max range from GetAmmoShootingDistance (helicopter range, per-weapon radar)");
        }
        catch(Exception e){MelonLogger.Error("FREEDOM_ARROW_RETICLE_FAILED: rangefinder keeps the game's range. "+e.Message);}
    }
    static void Log(string m){if(logs<60){logs++;MelonLogger.Msg("FREEDOM_ARROW_RETICLE "+m);}}
    public static unsafe void After(TargetLineSystem __instance,Entity __0,Entity __1)
    {
        if(broken||__instance==null||!Runtime.IsApplied)return;
        try
        {
            if(!__0.IsAlive||!__1.IsAlive)return;
            byte* sys=(byte*)__instance.Pointer;
            float dist=*(float*)(sys+0xA4);
            byte* list=*(byte**)(sys+0xA8);byte* buf=*(byte**)(sys+0xB8);int wn=*(int*)(sys+0xC0);
            if(list==null||buf==null||wn<=0)return;
            wn=Math.Min(wn,(int)*(long*)(buf+0x18));
            rounds.Clear();
            for(int i=0;i<wn;i++)
            {
                IntPtr wcp=*(IntPtr*)(buf+0x20+i*0x18);if(wcp==IntPtr.Zero)continue;
                var wc=new WeaponComponent(wcp);string wname=wc.WeaponInfo?.HUDName??"";
                byte* arr=*(byte**)((byte*)wcp+0x88);if(arr==null)continue;
                long n=*(long*)(arr+0x18);
                for(long j=0;j<n;j++)
                {
                    var ammo=BattleSystemHelpers.GetWeaponAmmunition(wc,*(int*)(arr+0x20+j*8));
                    if(ammo!=null)rounds[wname+"\n"+ammo.HUDName]=ammo;
                }
            }
            byte* items=*(byte**)(list+0x10);int size=*(int*)(list+0x18);if(items==null)return;
            size=Math.Min(size,(int)*(long*)(items+0x18));
            for(int i=0;i<size;i++)
            {
                byte* fl=*(byte**)(items+0x20+i*8);if(fl==null)continue;
                byte* st=*(byte**)(fl+0x10);int cnt=*(int*)(fl+0x18);if(st==null)continue;
                cnt=Math.Min(cnt,(int)*(long*)(st+0x18));
                for(int j=0;j<cnt;j++)
                {
                    byte* a=st+0x20+j*0x28;
                    string w=IL2CPP.Il2CppStringToManaged(*(IntPtr*)(a+8))??"",r=IL2CPP.Il2CppStringToManaged(*(IntPtr*)(a+0x10))??"";
                    if(!rounds.TryGetValue(w+"\n"+r,out var ammo)){Log($"no round found for {w} / {r}");continue;}
                    float old=*(float*)(a+0x24),max=BattleSystemHelpers.GetAmmoShootingDistance(__0,__1,ammo);
                    if(max<=0||Math.Abs(max-old)<0.5f)continue;
                    *(float*)(a+0x24)=max;a[1]=(byte)(dist>max?1:0);
                    Log($"{w} / {r} (round {ammo.Id}): max range {old:0} -> {max:0}, distance {dist:0}, out of range {a[1]==1}");
                }
            }
        }
        catch(Exception e){broken=true;MelonLogger.Error("FREEDOM_ARROW_RETICLE_FAILED: rangefinder keeps the game's range. "+e.Message);}
    }
}
