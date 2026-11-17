namespace BAModManager.Core;
// Only window branding/localization are replaced. File-list install, package records and paths are the launcher's own code.
static class AppInfo { public const string Id="BA-AssetsIndex-Test"; public static bool IsLauncher=>true; }
static class Loc { public static string T(string s,params object[] args)=>args.Length==0?s:string.Format(s,args); }
