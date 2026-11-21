namespace BAModManager.Core;
public static partial class Loc { public static string T(string s,params object[] a)=>a.Length==0?s:string.Format(s,a); }
