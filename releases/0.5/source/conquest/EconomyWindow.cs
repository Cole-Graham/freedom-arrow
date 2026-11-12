namespace FreedomArrow.Conquest;

// The exact transaction used by the runtime. Host checks cover rollback, not native income.
public readonly record struct EconomyState(bool Curve, float Upkeep, float Floor);
public sealed class EconomyWindow
{
    public bool Active { get; private set; }
    EconomyState original;
    public static float PerSecond(float perMinute)
    {
        if (!float.IsFinite(perMinute) || perMinute <= 0 || perMinute > 5000)
            throw new ArgumentOutOfRangeException(nameof(perMinute));
        return perMinute / 60f;
    }
    public void Begin(Func<EconomyState> read, Action<EconomyState> write)
    {
        if (Active) throw new InvalidOperationException("Nested economy update");
        original = read();
        Active = true; // Keep rollback available if a setter throws part-way through.
        write(new EconomyState(false, 0, 0));
    }
    public void End(Action<EconomyState> write)
    {
        if (!Active) return;
        write(original);
        Active = false; // A failed restore remains pending and can be retried.
    }
    // A new session owns its constructor/scenario values. Never restore an older snapshot over it.
    public void Discard() => Active = false;
}
