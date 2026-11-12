namespace FreedomArrow;

// Pure conservative policy. Unknown or mixed readiness retains native behavior.
static class AaCooldownPolicy
{
    public static bool ProjectileType(int type)=>type is 128 or 256 or 512 or 1024;
    public static bool Defender(int unitType,bool nativeAntiAir,bool interceptionGun)
        =>(unitType&(2|4|32))!=0&&(nativeAntiAir||interceptionGun);
    public readonly struct Contributor
    {
        public readonly ulong Weapon; public readonly float Remaining; public readonly bool Known,Airborne;
        public Contributor(ulong weapon,float remaining,bool known,bool airborne){Weapon=weapon;Remaining=remaining;Known=known;Airborne=airborne;}
    }
    public static bool ClearlyLate(float remaining, float impact)
        => float.IsFinite(remaining) && float.IsFinite(impact) && impact > .05f && impact <= 20
            && remaining >= 0 && remaining > impact * 1.25f + .25f + .35f;
    public static bool Release(bool original, bool groundCaller, bool includeBlocked,
        double ageSeconds, int incoming, ulong excludeWeapon, float impact, Contributor[] contributors)
    {
        if(!original || !groundCaller || includeBlocked || ageSeconds < 0 || ageSeconds > .075
            || incoming != 0 || contributors.Length == 0) return false;
        int counted = 0;
        foreach(var c in contributors)
        {
            // A live interceptor always retains native protection, even if its launcher is the excluded weapon.
            if(c.Airborne)return false;
            if(c.Weapon == excludeWeapon)continue;
            counted++;
            if(!c.Known || !ClearlyLate(c.Remaining, impact))return false;
        }
        return counted > 0;
    }
    public static float Remaining(float burst, float reload, float cycle)
        => float.IsFinite(burst) && float.IsFinite(reload) && float.IsFinite(cycle)
            ? Math.Max(0, Math.Max(burst, Math.Max(reload, cycle))) : float.NaN;
}
