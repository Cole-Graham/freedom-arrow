using System;
using System.IO;
using System.Linq;
using HarmonyLib;
using Il2CppBrokenArrow.Client.Ecs.Decks;
using MelonLoader;
namespace FreedomArrow;
// 0.9.0-dev.3 (Osama, 14 November 2026: "make sure that we don't touch vanilla folder, automatically").
// The game keeps decks as .dek files in <persistentDataPath>/Decks. At start, DeckService.Initialize (RVA 0x6E8F90) loads
// every file, runs TryFixDeck against the loaded tables and saves each deck it fixed (GetDataModel, 0x6ECDB0). With our
// tables loaded, that rewrote vanilla decks for good. The ctor (0x6EE010) sets DecksFolderPath (+0x10) =
// persistentDataPath + separator + "Decks" and _deckTrashPath (+0x48) = DecksFolderPath + a fixed suffix; every load,
// save, rename and delete reads those two fields. Before Initialize, both point into Decks/FreedomArrow. The deck list
// (GetDeckFileNames, 0x6E81A0) reads only the top folder, so vanilla never loads mod decks. On first run the vanilla
// decks are copied in; the mod then edits only the copies. Steam Cloud already syncs Decks subfolders.
static class DeckFolder
{
    public const string Sub="FreedomArrow";
    const string Marker="freedom-arrow-import.txt";
    public static void Install(HarmonyLib.Harmony h)
    {
        h.Patch(AccessTools.Method(typeof(DeckService),nameof(DeckService.Initialize)),prefix:new HarmonyMethod(typeof(DeckFolder),nameof(Before)){priority=Priority.First});
        MelonLogger.Msg("FREEDOM_ARROW_DECK_FOLDER: hook installed; mod decks live in Decks/"+Sub);
    }
    static void Before(DeckService __instance)
    {
        string vanilla=__instance.DecksFolderPath,trash=__instance._deckTrashPath;
        if(string.IsNullOrEmpty(vanilla)||Path.GetFileName(vanilla.TrimEnd('/','\\'))==Sub)return;
        string mod=Path.Combine(vanilla,Sub);
        // Paths first: if anything below fails, the game still never reads or writes the vanilla folder.
        __instance.DecksFolderPath=mod;
        __instance._deckTrashPath=trash!=null&&trash.StartsWith(vanilla,StringComparison.Ordinal)?mod+trash.Substring(vanilla.Length):Path.Combine(mod,"deleted");
        try
        {
            Directory.CreateDirectory(mod);
            int copied=0;
            if(!File.Exists(Path.Combine(mod,Marker))&&Directory.Exists(vanilla))
            {
                foreach(var f in Directory.GetFiles(vanilla,"*.dek",SearchOption.TopDirectoryOnly))
                {
                    var to=Path.Combine(mod,Path.GetFileName(f));
                    if(File.Exists(to))continue;
                    File.Copy(f,to);copied++;
                }
                File.WriteAllText(Path.Combine(mod,Marker),$"Freedom Arrow copied {copied} vanilla decks here on {DateTime.UtcNow:O}. Delete this file to copy missing vanilla decks again.\n");
            }
            int have=Directory.GetFiles(mod,"*.dek",SearchOption.TopDirectoryOnly).Length;
            MelonLogger.Msg($"FREEDOM_ARROW_DECK_FOLDER: decks={mod}; trash={__instance._deckTrashPath}; imported={copied}; mod_decks={have}; vanilla folder not used");
            DiagnosticLog.Write("deck_folder",new{mod,trash=__instance._deckTrashPath,imported=copied,mod_decks=have});
        }
        catch(Exception e)
        {
            MelonLogger.Error("FREEDOM_ARROW_DECK_FOLDER_IMPORT_FAILED: mod decks still use Decks/"+Sub+"; vanilla decks not copied. "+e.Message);
            DiagnosticLog.Write("deck_folder_failed",new{mod,error=e.ToString()});
        }
    }
}
