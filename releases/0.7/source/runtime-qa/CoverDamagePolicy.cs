namespace FreedomArrow;

// Share of damage taken after cover. Ammunition IgnoreCover removes protection in proportion.
public static class CoverDamagePolicy
{
    public static float Factor(float taken,float ignoreCover)
    {
        if(!float.IsFinite(taken)||taken<=0||taken>1)throw new ArgumentOutOfRangeException(nameof(taken));
        float ignore=float.IsFinite(ignoreCover)?Math.Clamp(ignoreCover,0,1):0;
        return 1-(1-taken)*(1-ignore);
    }
}
