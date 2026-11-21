/* Freedom Arrow Linux fix (20 Nov 2026): Proton games freeze with "Fatal error in GC / SuspendThread loop failed" when
   kernel.yama.ptrace_scope=1 blocks wineserver from tracing the game. This library, loaded with LD_PRELOAD, lets any process
   of the same user trace the process it is loaded into (PR_SET_PTRACER_ANY) - only that process, only while it runs.
   It changes no system setting and does nothing else. */
#include <sys/prctl.h>
#include <unistd.h>
#ifndef PR_SET_PTRACER
#define PR_SET_PTRACER 0x59616d61
#endif
#ifndef PR_SET_PTRACER_ANY
#define PR_SET_PTRACER_ANY ((unsigned long)-1)
#endif
__attribute__((constructor)) static void fa_ptracer(void) { prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY, 0, 0, 0); }
