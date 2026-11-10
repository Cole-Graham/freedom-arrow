using System.Text.Json;
using UnityEngine;
using MelonLoader;
using Il2CppBrokenArrow.Client.Ecs.Spawn;

namespace FAModels;

public partial class Mod
{
    // Optional, unit-scoped visual swaps. Native weapon objects retain firing, VFX and hand/back attachment logic.
    class InfantryWeaponRule
    {
        public int unitId { get; set; }
        public int soldierIndex { get; set; } = -1;
        public string slot { get; set; } = "primary";
        public int weaponId { get; set; }
        public string file { get; set; } = "";
        public string battle { get; set; } = "";
        public float scale { get; set; } = 1;
        public float[] offset { get; set; } = new float[3];
        public float[] rotation { get; set; } = new float[3];
    }
    class InfantryWeaponView
    {
        public UnitModelInfo model;
        public int unitId;
        public bool battle;
        public float created = Time.realtimeSinceStartup;
        public readonly HashSet<int> applied = new();
        public readonly HashSet<string> failed = new();
    }
    static List<InfantryWeaponRule> weaponRules = new();
    static readonly List<InfantryWeaponView> weaponViews = new();
    static float weaponPoll;
    static readonly Dictionary<string, Mesh[]> weaponMeshes = new();

    static void LoadWeaponRules()
    {
        var path = Path.Combine(dir, "infantry-weapons.json");
        if (!File.Exists(path)) return;
        try
        {
            var rules = JsonSerializer.Deserialize<List<InfantryWeaponRule>>(File.ReadAllText(path)) ?? new();
            foreach (var r in rules)
            {
                if (r.unitId <= 0 || r.soldierIndex < -1 || (r.slot != "primary" && r.slot != "special") ||
                    r.scale <= 0 || !float.IsFinite(r.scale) || r.offset.Length != 3 || r.rotation.Length != 3 ||
                    r.offset.Any(x => !float.IsFinite(x)) || r.rotation.Any(x => !float.IsFinite(x)) ||
                    string.IsNullOrWhiteSpace(r.file) || Path.GetFileName(r.file) != r.file ||
                    !File.Exists(Path.Combine(dir, r.file)) ||
                    (r.battle != "" && (Path.GetFileName(r.battle) != r.battle || !File.Exists(Path.Combine(dir, r.battle)))))
                    throw new InvalidDataException("Invalid infantry weapon rule; existing weapon visuals retained");
            }
            weaponRules = rules.OrderByDescending(r => r.soldierIndex >= 0).ThenByDescending(r => r.weaponId > 0).ToList();
            MelonLogger.Msg($"FAMODELS infantry weapon rules ready: {rules.Count}; visual only, native stats retained");
        }
        catch (Exception ex) { weaponRules.Clear(); MelonLogger.Error("FAMODELS infantry rules rejected: " + ex.Message); }
    }

    static void AfterInfantryWeapons(UnitModelInfo unitModel, Il2CppBrokenArrow.DataBase.Models.Units unitData, Il2CppBrokenArrow.Shared.Ecs.MemoryController.IUnitLoadScope scope)
    {
        if (unitModel != null && unitData != null) QueueBodies(unitModel, unitData.Id);
        if (unitModel != null && unitData != null)
            QueueWeapons(unitModel, unitData.Id, scope?.TryCast<Il2CppBrokenArrow.Client.Ecs.Controllers.BattleLifetime>() != null);
    }

    static void QueueWeapons(UnitModelInfo model, int unitId, bool battle)
    {
        if (!weaponRules.Any(r => r.unitId == unitId)) return;
        if (weaponViews.Any(x => x.model == model)) return;
        weaponViews.Add(new InfantryWeaponView { model = model, unitId = unitId, battle = battle });
    }

    static void TickInfantryWeapons()
    {
        if (Time.realtimeSinceStartup - weaponPoll < .25f) return;
        weaponPoll = Time.realtimeSinceStartup;
        for (int n = weaponViews.Count - 1; n >= 0; n--)
        {
            var view = weaponViews[n];
            if (view.model?.PrefabRootScript == null)
            {
                if (Time.realtimeSinceStartup - view.created > 30) weaponViews.RemoveAt(n);
                continue;
            }
            var soldiers = view.model.SquadSolders;
            if (soldiers == null) continue; // Infantry view construction completes asynchronously.
            for (int i = 0; i < soldiers.Length; i++)
            {
                var soldier = soldiers[i];
                if (soldier == null) continue;
                foreach (var r in weaponRules)
                {
                    if (r.unitId != view.unitId || (r.soldierIndex >= 0 && r.soldierIndex != i)) continue;
                    var weapon = r.slot == "special" ? soldier.SpecialWeapon : soldier.PrimaryWeapon;
                    if (weapon?.WeaponGameObject == null || weapon.Weapon == null) continue;
                    if (r.weaponId > 0 && weapon.Weapon.Id != r.weaponId) continue;
                    var go = weapon.WeaponGameObject;
                    int id = go.GetInstanceID();
                    string key = $"{i}:{r.slot}:{id}";
                    if (view.applied.Contains(id) || view.failed.Contains(key)) continue;
                    if (go.transform.Find("FAM_holder") != null) { view.applied.Add(id); continue; }
                    try
                    {
                        var e = new Entry { file = view.battle && r.battle != "" ? r.battle : r.file,
                            align = false, scale = r.scale, offset = r.offset };
                        Apply(go, e, $"infantry {view.unitId} soldier {i} {r.slot}", true);
                        var holder = go.transform.Find("FAM_holder");
                        if (holder != null) holder.localRotation = Quaternion.Euler(r.rotation[0], r.rotation[1], r.rotation[2]);
                        if (holder != null)
                        {
                            // Share identical geometry between soldiers, keeping native-like draw/memory costs.
                            var filters = holder.GetComponentsInChildren<MeshFilter>(true).ToArray();
                            if (weaponMeshes.TryGetValue(e.file, out var shared) && shared.Length == filters.Length)
                            {
                                for (int f = 0; f < filters.Length; f++)
                                {
                                    var duplicate = filters[f].sharedMesh;
                                    filters[f].sharedMesh = shared[f];
                                    if (duplicate != shared[f]) UnityEngine.Object.Destroy(duplicate);
                                }
                            }
                            else weaponMeshes[e.file] = filters.Select(f => f.sharedMesh).ToArray();
                            var renderers = holder.GetComponentsInChildren<MeshRenderer>(true).ToArray();
                            foreach (var renderer in renderers) if (renderer.sharedMaterial != null) renderer.sharedMaterial.enableInstancing = true;
                            // Measured native AK74M/RPK74M/SVD/M32 prefabs have a single LOD and 0.02 screen cutoff.
                            var group = holder.gameObject.AddComponent<LODGroup>();
                            var list = new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<LOD>(1);
                            list[0] = new LOD(.02f, new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<Renderer>(renderers.Cast<Renderer>().ToArray()));
                            group.SetLODs(list);
                            group.RecalculateBounds();
                        }
                        view.applied.Add(id);
                        MelonLogger.Msg($"FAMODELS weapon applied: unit={view.unitId} soldier={i} slot={r.slot} nativeWeapon={weapon.Weapon.Id} file={e.file}");
                    }
                    catch (Exception ex)
                    {
                        // The normal weapon must remain visible if mesh construction fails.
                        var holder = go.transform.Find("FAM_holder");
                        if (holder != null) UnityEngine.Object.Destroy(holder.gameObject);
                        if (origs.TryGetValue(id, out var original))
                        {
                            foreach (var renderer in original) if (renderer != null) renderer.forceRenderingOff = false;
                            origs.Remove(id);
                        }
                        view.failed.Add(key);
                        MelonLogger.Error($"FAMODELS weapon failed {key}: {ex.Message}; native visuals restored");
                    }
                }
            }
        }
    }
}
