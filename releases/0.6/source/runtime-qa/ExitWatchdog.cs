using System.Runtime.InteropServices;
namespace FreedomArrow;
// Exit watchdog (Osama 21 Nov 2026 23:06 PST, thread 1573561286803980289: "can we just have a simple task killer"). On his Linux PC (Proton)
// every exit on 21 Nov hung after the mods had shut down: our log upload, test-log bundle and MelonLoader's "Preferences Saved!" were done
// at 22:56:41, the window stayed up, and at 22:57:35 KWin's force-quit helper killed it (Unity's crash handler then started). Steam saw the
// game stop 1-3.5 minutes after quit on all 5 exits. Started at the end of our shutdown: if the process is still alive WaitSeconds later,
// it ends itself. A game that exits normally is gone before the timer fires (background thread), so nothing changes there.
static class ExitWatchdog
{
    const int WaitSeconds=10;
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr process,uint exitCode);
    static int started;
    public static void Start()
    {
        if(Interlocked.Exchange(ref started,1)==1)return;
        var t=new Thread(()=>
        {
            Thread.Sleep(WaitSeconds*1000);
            try{File.AppendAllText(Path.Combine(MelonLoader.Utils.MelonEnvironment.MelonLoaderLogsDirectory,"FreedomArrow-exit-watchdog.log"),
                $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} game still running {WaitSeconds} s after shutdown; process ended by the exit watchdog\n");}catch{}
            TerminateProcess(GetCurrentProcess(),0);
        }){IsBackground=true,Name="FreedomArrow exit watchdog"};
        t.Start();
    }
}
