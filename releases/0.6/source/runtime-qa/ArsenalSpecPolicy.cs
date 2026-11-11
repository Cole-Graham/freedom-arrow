namespace FreedomArrow;

// Presentation only: shared units retain every database availability.
internal static class ArsenalSpecPolicy
{
    internal static int GroupFor(int primary, IReadOnlyCollection<int> memberships, IReadOnlyCollection<int> selected)
    {
        if(selected.Count==0||selected.Contains(primary))return primary;
        int target=int.MaxValue;
        foreach(int spec in memberships)
            if(selected.Contains(spec)&&spec<target)target=spec;
        // The native filter hides non-matching units. Keep their original group.
        return target==int.MaxValue?primary:target;
    }
}
