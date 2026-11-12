namespace FAMusic;

// A marked opening track plays once per menu entry, before the regular playlist.
internal sealed class MenuSequence
{
    bool started;
    readonly Queue<string> remaining = new();
    public void Reset() { started = false; remaining.Clear(); }
    public string Next(IReadOnlyList<string> intro, IReadOnlyList<string> regular, Random random)
    {
        if (!started)
        {
            started = true;
            foreach (var file in intro.OrderBy(_ => random.Next())) remaining.Enqueue(file);
        }
        if (remaining.Count == 0)
            foreach (var file in (regular.Count > 0 ? regular : intro).OrderBy(_ => random.Next())) remaining.Enqueue(file);
        return remaining.Dequeue();
    }
}
