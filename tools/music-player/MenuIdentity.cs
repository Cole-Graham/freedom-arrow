namespace FAMusic;
internal static class MenuIdentity
{
    public static string Resolve(string displayLabel, string name, string version)
    {
        if (!string.IsNullOrWhiteSpace(displayLabel)) return displayLabel;
        return name == "Freedom Arrow" && !string.IsNullOrWhiteSpace(version) ? "Freedom Arrow " + version : null;
    }
}
