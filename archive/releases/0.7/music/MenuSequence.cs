namespace FAMusic;

// A marked opening track plays once per menu entry, before the regular playlist.
internal sealed class MenuSequence
{
    public static bool IsOrderedPack(string pack) => pack == "Black Hawk Down";
    public static float MenuGapSeconds(string pack) => pack == "Black Hawk Down" ? 120f : 0f;
    // Explicit names prevent legacy openers or unrelated menu files entering the new draw.
    public static List<string> CompilationFiles(string pack, string directory)
    {
        if (pack is not ("China" or "Black Hawk Down")) return new();
        return Enumerable.Range(1, 2)
            .Select(i => Path.Combine(directory, $"Menu - {pack} Compilation {i}.mp3"))
            .Where(File.Exists).ToList();
    }
    bool started;
    readonly Queue<string> remaining = new();
    public int Remaining => remaining.Count;
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
