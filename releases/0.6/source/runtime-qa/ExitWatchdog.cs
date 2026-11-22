using System.Runtime.InteropServices;
namespace FreedomArrow;
// Exit watchdog (Osama 21 Nov 2026 23:06 PST, thread 1573561286803980289: "can we just have a simple task killer"). On his Linux PC (Proton)
// every exit on 21 Nov hung after the mods had shut down: our log upload, test-log bundle and MelonLoader's "Preferences Saved!" were done
// at 22:56:41, the window stayed up, and at 22:57:35 KWin's force-quit helper killed it. Steam saw the game stop 1-3.5 minutes after quit.
// 0.9.5-dev.1 used a managed background thread: it never fired (23:31 test, still hung at 23:32), because the .NET runtime shuts down
// with MelonLoader and stops background threads before the native hang. Now a native thread-pool timer (kernel32 CreateTimerQueueTimer)
// calls kernel32 TerminateProcess(current process) WaitSeconds after the end of our shutdown; it needs no managed code when it fires.
// The callback is called as callback(parameter, TRUE), i.e. TerminateProcess(GetCurrentProcess() pseudo-handle -1, exit code 1).
// A game that exits normally is gone before the timer fires.
static class ExitWatchdog
{
    const uint WaitSeconds=10,WT_EXECUTEINTIMERTHREAD=0x20,WT_EXECUTEONLYONCE=0x8;
    [DllImport("kernel32.dll",CharSet=CharSet.Ansi)] static extern IntPtr GetModuleHandleA(string name);
    [DllImport("kernel32.dll",CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr module,string name);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CreateTimerQueueTimer(out IntPtr timer,IntPtr queue,IntPtr callback,IntPtr parameter,uint dueMs,uint periodMs,uint flags);
    static IntPtr timer;
    public static void Start()
    {
        if(timer!=IntPtr.Zero)return;
        var terminate=GetProcAddress(GetModuleHandleA("kernel32.dll"),"TerminateProcess");
        bool ok=terminate!=IntPtr.Zero&&CreateTimerQueueTimer(out timer,IntPtr.Zero,terminate,new IntPtr(-1),WaitSeconds*1000,0,WT_EXECUTEINTIMERTHREAD|WT_EXECUTEONLYONCE);
        try{File.AppendAllText(Path.Combine(MelonLoader.Utils.MelonEnvironment.MelonLoaderLogsDirectory,"FreedomArrow-exit-watchdog.log"),
            $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {(ok?"armed":"NOT armed (error "+Marshal.GetLastWin32Error()+")")}: the game ends itself {WaitSeconds} s after shutdown if it is still running\n");}catch{}
        MelonLoader.MelonLogger.Msg($"FREEDOM_ARROW_EXIT_WATCHDOG {(ok?"armed":"not armed")}: native timer ends the process {WaitSeconds} s from now if it hangs");
    }
}
