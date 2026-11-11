namespace FreedomArrow;

// Pure identity check; the caller verifies package and infantry hashes before showing it.
public static class BuildIdentity
{
    public static string ResolveLabel(string compiledVersion,string packageVersion,int build,string label)
    {
        if(build<1 || compiledVersion!=build.ToString() || packageVersion!=compiledVersion || label!="PLA TEST Build "+compiledVersion)
            throw new InvalidDataException("PLA build identity mismatch between runtime, channel and complete package");
        return label;
    }
}
