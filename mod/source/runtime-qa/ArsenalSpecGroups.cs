using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks_v2.UI;
using Il2CppBrokenArrow.DataBase.Models;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;

namespace FreedomArrow;

// Keep native buttons, filtering, cards and callbacks. Reassign the existing
// normal/photo cards to an eligible selected heading after native filtering.
static class ArsenalSpecGroups
{
    sealed class Spec
    {
        internal readonly int Id,Flag;
        internal Spec(int id,int flag){Id=id;Flag=flag;}
    }
    sealed class Change
    {
        internal readonly CountrySpecializationUnitGroup Group;
        internal readonly Il2CppReferenceArray<HangarUnitCardScript> Before,After;
        internal Change(CountrySpecializationUnitGroup group,Il2CppReferenceArray<HangarUnitCardScript> before,Il2CppReferenceArray<HangarUnitCardScript> after)
        {Group=group;Before=before;After=after;}
    }
    static readonly Dictionary<IntPtr,Spec> specs=new();
    static readonly Dictionary<IntPtr,(int Mask,IntPtr Scroll)> applied=new();
    static bool enabled;

    internal static void Install(HarmonyLib.Harmony harmony,bool plaOnly)
    {
        enabled=plaOnly;
        if(!enabled)return;
        harmony.Patch(AccessTools.Method(typeof(SpecializationFilterButton),"Initialize"),
            postfix:new HarmonyMethod(typeof(ArsenalSpecGroups),nameof(SpecReady)));
        harmony.Patch(AccessTools.Method(typeof(SpecializationFilterButton),"Release"),
            prefix:new HarmonyMethod(typeof(ArsenalSpecGroups),nameof(SpecReleased)));
        harmony.Patch(AccessTools.Method(typeof(HangarUnitFilter),"ApplyFilter"),
            postfix:new HarmonyMethod(typeof(ArsenalSpecGroups),nameof(Apply)));
        harmony.Patch(AccessTools.Method(typeof(HangarUnitFilter),"Release"),
            prefix:new HarmonyMethod(typeof(ArsenalSpecGroups),nameof(FilterReleased)));
        MelonLogger.Msg("PLA_SPEC_GROUPS hooks installed; native filtering retained; shared cards follow selected specialization");
    }
    public static void SpecReady(SpecializationFilterButton __instance,int filterFlag,Specializations specialization)
    {
        if(enabled&&specialization.CountryId==4)
            specs[__instance.Pointer]=new(specialization.Id,filterFlag);
    }
    public static void SpecReleased(SpecializationFilterButton __instance)=>specs.Remove(__instance.Pointer);
    public static void FilterReleased(HangarUnitFilter __instance)=>applied.Remove(__instance.Pointer);

    static void Plan(Il2CppSystem.Collections.Generic.Dictionary<HangarUnitCardModel,HangarUnitCardScript> cards,
        Il2CppReferenceArray<CountrySpecializationUnitGroup> groups,HashSet<int> china,HashSet<int> selected,List<Change> changes)
    {
        if(cards==null||groups==null)throw new InvalidOperationException("Arsenal card groups not initialized");
        var byId=new Dictionary<int,CountrySpecializationUnitGroup>();
        var buckets=new Dictionary<int,List<HangarUnitCardScript>>();
        foreach(var group in groups)
            if(china.Contains(group._specializationId))
            {
                byId.Add(group._specializationId,group);
                buckets.Add(group._specializationId,new());
            }
        // Plan both modes completely before touching the hierarchy.
        foreach(var pair in cards)
        {
            var card=pair.Value;
            if(card.Unit.CountryId!=4)continue;
            var memberships=new List<int>();
            foreach(int id in card.Unit.SpecializationIds)memberships.Add(id);
            if(memberships.Count==0)throw new InvalidOperationException("China unit has no specialization: "+card.Unit.Id);
            int target=ArsenalSpecPolicy.GroupFor(memberships[0],memberships,selected);
            if(!buckets.TryGetValue(target,out var bucket))
                throw new InvalidOperationException("Missing Arsenal heading for specialization "+target);
            bucket.Add(card);
        }
        foreach(var pair in byId)
            changes.Add(new(pair.Value,pair.Value._unitCards,new(buckets[pair.Key].ToArray())));
    }
    static void Set(Change change,Il2CppReferenceArray<HangarUnitCardScript> cards)
    {
        var group=change.Group;
        // Native Initialize sets each card's parent and group reference, while
        // retaining the heading and its normal/photo visibility callback.
        group.Initialize(group._specializationId,cards,group._isPhotoCardMode,group._canChangeVisibility);
    }
    public static void Apply(HangarUnitFilter __instance)
    {
        if(!enabled||!Runtime.IsApplied||!__instance._isInitialized)return;
        var scroll=__instance._unitScroll;
        if(scroll==null)return;
        int mask=__instance._filterFlags;
        if(applied.TryGetValue(__instance.Pointer,out var previous)&&previous==(mask,scroll.Pointer))return;
        var changes=new List<Change>();bool mutated=false;
        try
        {
            var china=new HashSet<int>();var selected=new HashSet<int>();
            foreach(var country in __instance._countryFilterButtonsGroups)
            {
                if(country._buttons==null)continue;
                foreach(var button in country._buttons)
                    if(specs.TryGetValue(button.Pointer,out var spec))
                    {
                        china.Add(spec.Id);
                        if((mask&spec.Flag)!=0)selected.Add(spec.Id);
                    }
            }
            if(china.Count==0)return;
            Plan(scroll._cards,scroll._cardGroups,china,selected,changes);
            Plan(scroll._photoCards,scroll._photoCardGroups,china,selected,changes);
            mutated=true;
            foreach(var change in changes)Set(change,change.After);
            foreach(var change in changes)change.Group.TryChangeVisibility();
            scroll.UpdateCardsVisibility(true,true);
            applied[__instance.Pointer]=(mask,scroll.Pointer);
            MelonLogger.Msg($"PLA_SPEC_GROUPS_APPLIED mask={mask} selected=[{string.Join(",",selected.OrderBy(x=>x))}] groups={changes.Count} cards={changes.Sum(c=>c.After.Length)}");
        }
        catch(Exception e)
        {
            if(mutated)
            {
                try
                {
                    foreach(var change in changes)Set(change,change.Before);
                    foreach(var change in changes)change.Group.TryChangeVisibility();
                    scroll.UpdateCardsVisibility(true,true);
                }
                catch(Exception restore){MelonLogger.Error("PLA_SPEC_GROUPS_RESTORE_FAILED: "+restore);}
            }
            MelonLogger.Error("PLA_SPEC_GROUPS_FAILED; native filter retained: "+e);
        }
    }
}
