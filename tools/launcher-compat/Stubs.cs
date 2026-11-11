namespace BAModManager.Core;
// Only window branding/localization are replaced. Package planning, install, activation and matching are upstream.
static class AppInfo { public const string Id="BA-Launcher-Compatibility-Only"; public static bool IsLauncher=>true; }
static class Loc { public static string T(string s,params object[] args)=>args.Length==0?s:string.Format(s,args); }
