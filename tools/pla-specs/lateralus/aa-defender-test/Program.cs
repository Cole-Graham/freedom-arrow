using FreedomArrow;
int n=0,fail=0;void T(bool c,string l){n++;if(!c){fail++;Console.WriteLine("FAIL "+l);}}
// Real 0.8 rounds: Pantsir 1983, M-SHORAD 1967, Zubr AK-630 191; MANPADS-style air-only 24; ground-only 7.
T(AaCooldownPolicy.Defender(4,true,true,1983),"Pantsir gun");
T(AaCooldownPolicy.Defender(4,true,false,1920),"SAM with projectile bits");
T(AaCooldownPolicy.Defender(32,false,true,191),"Zubr AK-630");
T(!AaCooldownPolicy.Defender(4,true,false,24),"air-only SAM excluded");
T(!AaCooldownPolicy.Defender(2,true,false,24),"MANPADS excluded");
T(!AaCooldownPolicy.Defender(4,false,false,1983),"non-AA weapon excluded");
T(!AaCooldownPolicy.Defender(8,true,true,1983),"helicopter excluded");
T(!AaCooldownPolicy.Defender(16,true,false,1920),"aircraft excluded");
foreach(long b in new long[]{128,256,512,1024})T(AaCooldownPolicy.Defender(4,true,false,b),"bit "+b);
T(AaCooldownPolicy.MaxDefenders==128,"limit");
Console.WriteLine($"{n-fail}/{n} pass");return fail;
