"""Run the player's actual menu/update methods with a fake clock and FMOD channel.

No Unity or sound device is required. Source methods are copied without edits.
"""
from pathlib import Path
import os, subprocess, sys

here = Path(__file__).resolve().parent
source = Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / 'music-player/FAMusic.cs'
text = source.read_text()
def method(signature):
    start = text.index('    ' + signature)
    brace = text.index('{', start)
    depth, end = 1, brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

methods = '\n'.join(method(s) for s in ['public override void OnUpdate()', 'static void PlayNext()', 'static void StopTrack()', 'static void Switch(', 'static string FolderFor('])
prefix = r'''
using System.Text;
namespace FAMusic;
class FixedRandom(int choice) : Random { public override int Next(int max) { if(max!=2)throw new Exception("Expected two choices"); return choice; } }
class Base { public virtual void OnUpdate() {} }
class Logger { public readonly List<string> Lines = new(); public void Msg(string s)=>Lines.Add(s); public void Warning(string s)=>Lines.Add(s); }
class Melon<T> { public static Logger Logger = new(); }
static class UnityEngine { public static class Time { public static float time, unscaledTime; } }
static class Fmod {
 public static bool Playing; public static List<string> Started = new();
 public static int FMOD_Channel_IsPlaying(IntPtr c,out int p) { p=Playing?1:0; return 0; }
 public static int FMOD_Channel_Stop(IntPtr c) { Playing=false;return 0; }
 public static int FMOD_Sound_Release(IntPtr c)=>0;
 public static int FMOD_System_Update(IntPtr c)=>0;
 public static int FMOD_Channel_SetVolume(IntPtr c,float v)=>0;
 public static int FMOD_System_CreateSound(IntPtr s,byte[] file,int mode,IntPtr extra,out IntPtr result) { Started.Add(Encoding.UTF8.GetString(file).TrimEnd('\0'));result=(IntPtr)2;return 0; }
 public static int FMOD_System_PlaySound(IntPtr s,IntPtr sound,IntPtr group,int paused,out IntPtr c) { Playing=true;c=(IntPtr)3;return 0; }
}
static class MusicMenu { public static void Update(){} }
class Service { public Instance CurrentInstance = new(); }
class Instance { public void SetVolume(float x){} }
partial class Player : Base {
 static string Root=Path.Combine(Path.GetTempPath(),"fa-music-test-"+Guid.NewGuid()), PacksDir=Path.Combine(Root,"Packs");
 static string pack="Black Hawk Down",folder,playingDir;
 const string GameMusic="Game music";
 static float resumeAt,battleStart=-1,volume=.086f,slider=1;
 const float BattleGap=120,CalmGap=10;
 static bool playedOnce;
 static IntPtr system=(IntPtr)1,sound,channel;
 static Service service=new();
 static Random Rng=new(42);
 static Dictionary<string,List<string>> queues=new();
 static MenuSequence menuSequence=new();
 static int OpeningSeconds()=>300;
 static void ReadSlider(){} static void MuteGameMusic(){}
 static List<string> Files(string d)=>Directory.Exists(d)?Directory.GetFiles(d).Where(p=>p.EndsWith(".mp3")).ToList():new();
'''
suffix = r'''
 static void Check(bool ok,string msg) { if(!ok)throw new Exception(msg); }
 static void FileAt(string p) { p=Path.Combine(PacksDir,p);Directory.CreateDirectory(Path.GetDirectoryName(p));File.WriteAllText(p,""); }
 static string Last=>Path.GetFileName(Fmod.Started.Last());
 static void End(Player p,float t) { Fmod.Playing=false;UnityEngine.Time.unscaledTime=t;p.OnUpdate(); }
 static void Gap(Player p,float t,float gap) {
  int count=Fmod.Started.Count;End(p,t);
  Check(Fmod.Started.Count==count,"Track restarted before gap");
  UnityEngine.Time.unscaledTime=t+gap-.01f;p.OnUpdate();Check(Fmod.Started.Count==count,"Track started early");
  UnityEngine.Time.unscaledTime=t+gap;p.OnUpdate();Check(Fmod.Started.Count==count+1,"Track did not start at gap boundary");
 }
 public static void Main() {
  try {
   FileAt("Black Hawk Down/Menu/GLA11.mp3");
   foreach(var i in Enumerable.Range(1,10))FileAt($"Black Hawk Down/Battle/GLA{i:00}.mp3");
   FileAt("China/Menu/First/China11.mp3");FileAt("China/Menu/China01.mp3");
   FileAt("USA/Menu/USA1.mp3");FileAt("USA/Menu/USA2.mp3");FileAt("USA/Battle/Combat.mp3");FileAt("USA/Battle/Calm/Calm.mp3");FileAt("USA/Victory/Win.mp3");
   Check(MenuIdentity.Resolve(null,"Freedom Arrow","0.7.0-dev.45")=="Freedom Arrow 0.7.0-dev.45","LIVE locked version label");
   Check(MenuIdentity.Resolve(null,"Freedom Arrow","0.7.0-dev.55")=="Freedom Arrow 0.7.0-dev.55","LIVE main version label");
   Check(MenuIdentity.Resolve("PLA TEST Build 23","PLA TEST","23")=="PLA TEST Build 23","PLA label retained");
   Check(MenuIdentity.Resolve(null,null,null)==null,"Unknown identity leaves native label enabled");
   var p=new Player();Switch(FolderFor(20));p.OnUpdate();Check(Last=="GLA11.mp3","GLA opener wrong");
   var cycle=new List<string>();
   for(int i=0;i<10;i++){Gap(p,1000+i*500,120);cycle.Add(Last);}
   Check(cycle.Distinct().Count()==10&&!cycle.Contains("GLA11.mp3"),"GLA cycle repeated or replayed opener");
   Check(!cycle.SequenceEqual(cycle.OrderBy(x=>x)),"GLA cycle not shuffled");
   Gap(p,7000,120);Check(Last!="GLA11.mp3","GLA opener relooped");
   End(p,7500);Switch(FolderFor(20));int n=Fmod.Started.Count;UnityEngine.Time.unscaledTime=7550;p.OnUpdate();Check(Fmod.Started.Count==n,"Duplicate cue cancelled gap");
   pack="China";Switch(FolderFor(20));p.OnUpdate();Check(Last=="China11.mp3","China theme11 not first");
   End(p,8000);Check(Last=="China01.mp3","China second track wrong");
   End(p,8500);Check(Last=="China01.mp3","China opener repeated within menu session");
   Switch(null);Switch(FolderFor(20));p.OnUpdate();Check(Last=="China11.mp3","China opener not reset on menu entry");
   pack="USA";Switch(FolderFor(20));p.OnUpdate();n=Fmod.Started.Count;End(p,9000);Check(Fmod.Started.Count==n+1,"USA timing changed");
   Switch(FolderFor(50));p.OnUpdate();Check(Last=="Calm.mp3","Calm selection wrong");Gap(p,9500,10);
   battleStart=0;UnityEngine.Time.time=400;Switch(null);Switch(FolderFor(50));p.OnUpdate();Check(Last=="Combat.mp3","Combat selection wrong");Gap(p,10000,120);
   Switch(FolderFor(62));p.OnUpdate();n=Fmod.Started.Count;End(p,11000);Check(Fmod.Started.Count==n&&playedOnce,"Victory replayed");
   foreach(var which in new[]{"China","Black Hawk Down"}) {
    FileAt($"{which}/Menu/Menu - {which} Compilation 1.mp3");
    FileAt($"{which}/Menu/Menu - {which} Compilation 2.mp3");
    FileAt($"{which}/Menu/stray legacy opener.mp3");
    pack=which;Switch(null);Switch(FolderFor(20));
    Rng=new FixedRandom(0);p.OnUpdate();Check(Last==$"Menu - {which} Compilation 1.mp3","First RNG outcome wrong");
    Rng=new FixedRandom(1);n=Fmod.Started.Count;End(p,12000);
    Check(Fmod.Started.Count==n+1&&Last==$"Menu - {which} Compilation 2.mp3","Second outcome or extra menu delay wrong");
    n=Fmod.Started.Count;Switch(FolderFor(20));p.OnUpdate();Check(Fmod.Started.Count==n,"Duplicate cue interrupted compilation");
    Rng=new Random(42);var draws=new Dictionary<string,int>();
    for(int i=0;i<4000;i++){End(p,13000+i);draws[Last]=draws.GetValueOrDefault(Last)+1;}
    Check(draws.Count==2&&draws.Values.All(v=>v>1800&&v<2200),"Equal draw smoke check or legacy file exclusion failed");
    Console.WriteLine($"PASS {which}: two choices, each forced RNG outcome, no extra gap, duplicate cue retained; 4000 draws: {string.Join(", ",draws.Values)}");
   }
   Console.WriteLine("PASS legacy playback compatibility, new compiled menus, USA timing, battle120s/calm10s, victory once; simulated clock/FMOD only.");
  } finally { Directory.Delete(Root,true); }
 }
}
'''
(here/'Generated.cs').write_text(prefix+methods+suffix)
(here/'MenuIdentity.cs').write_text(source.resolve().with_name('MenuIdentity.cs').read_text())
(here/'Test.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup><Compile Include="'+os.path.relpath(source.resolve().with_name('MenuSequence.cs'),here)+'" Link="MenuSequence.cs" /></ItemGroup></Project>')
subprocess.run([sys.argv[2] if len(sys.argv)>2 else 'dotnet','run','--project',str(here/'Test.csproj'),'-c','Release'],check=True)
