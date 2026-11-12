namespace FreedomArrow;
// These are coexisting observations, never exclusive native rejection reasons.
static class AaObservationPolicy
{
    public static bool? AimingInProgress(bool componentPresent,float? secondsRemaining)
    {
        if(!componentPresent)return false;
        if(!secondsRemaining.HasValue||!float.IsFinite(secondsRemaining.Value))return null;
        return secondsRemaining.Value>0;
    }
    public static string[] Describe(bool enabled,bool hold,int ammo,bool reload,bool burst,bool cycle,bool aiming,bool selected,bool canAim,bool margin)
    {
        var notes=new List<string>();
        if(!enabled)notes.Add("weapon_disabled");
        if(hold)notes.Add("hold_fire_component_present");
        if(ammo<=0)notes.Add("empty_magazine");
        if(reload)notes.Add("magazine_reloading");
        if(burst)notes.Add("burst_cooldown");
        if(cycle)notes.Add("weapon_cycle_active");
        if(aiming)notes.Add("aiming_in_progress");
        if(!selected)notes.Add("no_selected_target_native_reason_unknown");
        else
        {
            if(!canAim)notes.Add("selected_target_can_aim_false");
            if(!margin)notes.Add("selected_target_outside_margin");
        }
        return notes.ToArray();
    }
}
