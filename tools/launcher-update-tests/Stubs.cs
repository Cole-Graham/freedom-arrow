namespace BAModManager.Core;
// Only window branding/localization are replaced. Package planning, install, activation and matching are upstream.
static class AppInfo { public const string Id="BA-Launcher-Update-Test"; public static bool IsLauncher=>true; }
static class Loc { public static string T(string s,params object[] args)=>args.Length==0?s:string.Format(s,args); }
public enum LaunchStage { Launcher, Mod, Loader, Assets, Verify, Start }
public sealed record LaunchProgress(string Text, double? Fraction = null, LaunchStage? Stage = null, long? Done = null, long? Total = null, string? Note = null);
