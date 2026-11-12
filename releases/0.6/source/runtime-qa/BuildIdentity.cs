namespace FreedomArrow;

// Pure identity check; the caller verifies package and infantry hashes before showing it.
// PLA TEST Build N (internal test builds) or Freedom Arrow <version> (0.8 live line, Osama 12 Nov 2026).
public static class BuildIdentity
{
    public static string ResolveLabel(string compiledVersion,string packageVersion,int build,string label)
    {
        bool test=compiledVersion==build.ToString() && label=="PLA TEST Build "+compiledVersion;
        bool release=label=="Freedom Arrow "+compiledVersion;
        if(build<1 || packageVersion!=compiledVersion || !(test||release))
            throw new InvalidDataException("Build identity mismatch between runtime, channel and complete package");
        return label;
    }
}
