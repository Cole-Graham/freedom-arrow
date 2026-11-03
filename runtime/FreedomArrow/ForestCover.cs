using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using HarmonyLib;
using Il2CppInterop.Runtime;
using MelonLoader;

namespace FreedomArrow;

static class ForestCover
{
    static readonly string[] Requires = { "InfantryUnitComponent", "TerrainTypeComponent" };
    const string Formula = "damage * (1 - reduction * (1 - clamp(IgnoreCover, 0, 1)))";

    static float _reduction;
    static int _terrainOffset = int.MinValue;
    static bool _logged;

    public static void Install(string root, MelonLogger.Instance log)
    {
        var path = Path.Combine(root, "formulas", "BattleSystemHelpers", "CalculateHitDamage.json");
        if (!File.Exists(path))
        {
            log.Msg("no CalculateHitDamage formula; damage postfix not installed");
            return;
        }
        try
        {
            _reduction = Read(path);
        }
        catch (Exception ex)
        {
            log.Error("formula startup aborted; CalculateHitDamage left unpatched: " + ex.Message);
            return;
        }
        try
        {
            var helpers = AccessTools.TypeByName("Il2CppBrokenArrow.Client.Ecs.BattleSystem.BattleSystemHelpers")
                ?? AccessTools.TypeByName("BrokenArrow.Client.Ecs.BattleSystem.BattleSystemHelpers");
            var method = AccessTools.Method(helpers, "CalculateHitDamage");
            if (method == null)
                throw new MissingMethodException("BattleSystemHelpers.CalculateHitDamage");
            var postfix = HookBinder.Postfix(method, typeof(ForestCover).GetMethod(nameof(Apply), BindingFlags.Public | BindingFlags.Static)!);
            new HarmonyLib.Harmony("freedomarrow.gameplay.forest").Patch(method, postfix: new HarmonyMethod(postfix));
            log.Msg("HOOK OK BattleSystemHelpers.CalculateHitDamage");
        }
        catch (Exception ex)
        {
            log.Error("formula startup aborted; CalculateHitDamage left unpatched: " + ex.Message);
        }
    }

    public static void Apply(object? target, object? ammo, ref float result)
    {
        if (target == null || result <= 0f)
            return;
        var infantry = FindType(
            "Il2CppBrokenArrow.Client.Ecs.Infantry.Components.InfantryUnitComponent",
            "BrokenArrow.Client.Ecs.Infantry.Components.InfantryUnitComponent");
        var terrain = FindType(
            "Il2CppBrokenArrow.Shared.Ecs.Components.Movement.TerrainTypeComponent",
            "BrokenArrow.Shared.Ecs.Components.Movement.TerrainTypeComponent");
        if (infantry == null || terrain == null)
            return;
        if (!Has(target, infantry) || !Has(target, terrain))
            return;
        if (_terrainOffset == int.MinValue)
            _terrainOffset = FieldOffset(terrain, "Value");
        var value = ReadByte(target, terrain);
        if (value != 2)
            return;
        var ignore = 0f;
        try
        {
            if (ammo != null)
            {
                var raw = ammo.GetType().GetProperty("IgnoreCover")?.GetValue(ammo);
                if (raw != null)
                    ignore = Math.Clamp(Convert.ToSingle(raw), 0f, 1f);
            }
        }
        catch
        {
            ignore = 0f;
        }
        var factor = _reduction * (1f - ignore);
        if (factor <= 0f)
            return;
        var before = result;
        result = before * (1f - factor);
        if (!_logged)
        {
            _logged = true;
            Melon<FreedomArrowMod>.Logger.Msg($"forest hit {before} -> {result}");
        }
    }

    static float Read(string path)
    {
        using var document = JsonDocument.Parse(File.ReadAllText(path));
        var root = document.RootElement;
        var keys = root.EnumerateObject().Select(property => property.Name).ToHashSet();
        string[] expected = { "method", "change", "requires", "terrain", "formula", "reduction", "damage", "IgnoreCover" };
        if (!keys.SetEquals(expected))
            throw new InvalidDataException("formula keys are not the forest cover postfix");
        if (root.GetProperty("method").GetString() != "BrokenArrow.Client.Ecs.BattleSystem.BattleSystemHelpers.CalculateHitDamage")
            throw new InvalidDataException("formula method is not CalculateHitDamage");
        if (root.GetProperty("change").GetString() != "after")
            throw new InvalidDataException("formula change is not after");
        var requires = root.GetProperty("requires").EnumerateArray().Select(item => item.GetString() ?? "").ToArray();
        if (!requires.SequenceEqual(Requires))
            throw new InvalidDataException("formula requires InfantryUnitComponent and TerrainTypeComponent");
        if (root.GetProperty("terrain").GetString() != "TerrainType.Forest")
            throw new InvalidDataException("formula terrain is not TerrainType.Forest");
        if (root.GetProperty("formula").GetString() != Formula)
            throw new InvalidDataException("formula text is not the forest cover postfix");
        if (root.GetProperty("damage").GetString() != "return" || root.GetProperty("IgnoreCover").GetString() != "Ammunitions.IgnoreCover")
            throw new InvalidDataException("formula inputs are not the return value and Ammunitions.IgnoreCover");
        var reduction = root.GetProperty("reduction").GetDouble();
        if (reduction < 0 || reduction > 1)
            throw new InvalidDataException("reduction must be a number from 0 to 1");
        return (float)reduction;
    }

    static bool Has(object entity, Type component)
    {
        var method = typeof(ForestCover).GetMethod(nameof(HasTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (bool)method.MakeGenericMethod(entity.GetType()).Invoke(null, new[] { entity, component })!;
    }

    static byte ReadByte(object entity, Type component)
    {
        var method = typeof(ForestCover).GetMethod(nameof(ReadTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (byte)method.MakeGenericMethod(entity.GetType()).Invoke(null, new[] { entity, component })!;
    }

    static bool HasTyped<T>(object boxed, Type component) where T : struct
    {
        var entity = (T)boxed;
        return HasNative(ref entity, component);
    }

    static byte ReadTyped<T>(object boxed, Type component) where T : struct
    {
        var entity = (T)boxed;
        var pointer = GetPtr(ref entity, component);
        unsafe
        {
            return *((byte*)pointer + _terrainOffset);
        }
    }

    unsafe static bool HasNative<T>(ref T entity, Type component) where T : struct
    {
        var method = Store(typeof(T), "MethodInfoStoreGeneric_Has_Public_Boolean_0`1", component);
        IntPtr thrown = IntPtr.Zero;
        var result = IL2CPP.il2cpp_runtime_invoke(method, (IntPtr)Unsafe.AsPointer(ref entity), (void**)null, ref thrown);
        Il2CppException.RaiseExceptionIfNecessary(thrown);
        if (result == IntPtr.Zero)
            return false;
        return *(bool*)IL2CPP.il2cpp_object_unbox(result);
    }

    unsafe static IntPtr GetPtr<T>(ref T entity, Type component) where T : struct
    {
        var method = Store(typeof(T), "MethodInfoStoreGeneric_Get_Public_byref_T_0`1", component);
        var code = *(IntPtr*)method;
        if (code == IntPtr.Zero)
            throw new InvalidOperationException("il2cpp has no Entity.Get for " + component.Name);
        var function = (delegate* unmanaged<T*, IntPtr, IntPtr>)code;
        return function((T*)Unsafe.AsPointer(ref entity), method);
    }

    static IntPtr Store(Type entity, string nested, Type component)
    {
        var open = entity.GetNestedType(nested, BindingFlags.Public | BindingFlags.NonPublic)
            ?? throw new MissingMemberException(entity.Name + "." + nested);
        var closed = open.MakeGenericType(component);
        RuntimeHelpers.RunClassConstructor(closed.TypeHandle);
        var field = closed.GetField("Pointer", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
            ?? throw new MissingFieldException(nested + ".Pointer");
        var pointer = (IntPtr)field.GetValue(null)!;
        if (pointer == IntPtr.Zero)
            throw new InvalidOperationException($"il2cpp has no {nested}<{component.Name}>");
        return pointer;
    }

    static int FieldOffset(Type component, string name)
    {
        var store = typeof(Il2CppClassPointerStore<>).MakeGenericType(component);
        var klass = (IntPtr)store.GetField("NativeClassPtr")!.GetValue(null)!;
        var field = IL2CPP.il2cpp_class_get_field_from_name(klass, name);
        if (field == IntPtr.Zero)
            throw new MissingFieldException(component.Name + "." + name);
        return (int)IL2CPP.il2cpp_field_get_offset(field) - 2 * IntPtr.Size;
    }

    static Type? FindType(params string[] names)
    {
        foreach (var name in names)
        {
            var found = AccessTools.TypeByName(name);
            if (found != null)
                return found;
        }
        return null;
    }
}
