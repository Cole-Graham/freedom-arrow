using System.Diagnostics;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using HarmonyLib;
using Il2CppInterop.Runtime;
using MelonLoader;

namespace FreedomArrow;

static class GroundSpotting
{
    public const string Method = "BrokenArrow.Client.Ecs.FogOfWar.FogOfWarUnit.CalculateVisionRangeForTarget";

    const string ScanMethod = "GetMaxOpticsCheckDistance";
    const string ExpectedHash = "12e7088369539b029a7bf0064062ce030a53b5189e7067420903f47b4281fddf";

    sealed class Signature
    {
        public Signature(int weaponId, float factor, double expiry)
        {
            WeaponId = weaponId;
            Factor = factor;
            Expiry = expiry;
        }

        public int WeaponId { get; }
        public float Factor { get; set; }
        public double Expiry { get; set; }
    }

    static readonly object Gate = new();
    static readonly Dictionary<long, List<Signature>> Signatures = new();
    static readonly Dictionary<long, float> LastEffective = new();
    static readonly HashSet<long> Dirty = new();
    static readonly Dictionary<int, (float Noise, float Vehicle)> Weapons = new();

    static MelonLogger.Instance? _log;
    static bool _active;
    static bool _trace;
    static bool _failed;
    static int _loggedRanges;
    static int _visionHarmonyCalls;
    static int _scanHarmonyCalls;
    static int _shotCalls;
    static int _weaponPointerMode;
    static double _now;

    static float _cap = 1076.923076923f;
    static float _exceptionalCap = 1292.307692308f;
    static float _exceptionalOptics = 2550f;
    static float _forestCover = 3f;
    static float _buildingCover = 4f;
    static float _windowSeconds = 5f;
    static float _spottedPenalty = 1.5f;

    static Type? _entityType;
    static Type? _fogType;
    static Type? _terrainType;
    static Type? _sneakType;
    static Type? _smokeType;
    static Type? _helicopterType;
    static Type? _aircraftType;
    static Type? _infantryType;
    static Type? _labelType;
    static Type? _parentType;
    static Type? _weaponType;
    static int _fogDistance = int.MinValue;
    static int _fogAnti = int.MinValue;
    static int _fogFlash = int.MinValue;
    static int _fogPenalty = int.MinValue;
    static int _fogUpdate = int.MinValue;
    static int _terrainValue = int.MinValue;
    static int _sneakEnabled = int.MinValue;
    static int _labelCrit = int.MinValue;
    static int _parentRoot = int.MinValue;
    static int _parentValue = int.MinValue;
    static int _weaponInfo = int.MinValue;
    static int _weaponId = int.MinValue;
    static int _weaponFlash = int.MinValue;
    static PropertyInfo? _deltaTime;

    [ThreadStatic]
    static int _depth;

    public static void Install(JsonElement parameters, MelonLogger.Instance log)
    {
        _log = log;
        ReadParameters(parameters);
        var module = FindModule();
        var actual = Hash(module.FileName ?? "");
        if (!string.Equals(actual, _expectedHash, StringComparison.OrdinalIgnoreCase))
        {
            log.Error("spotting left unpatched; GameAssembly hash " + actual);
            return;
        }
        ParseRva(parameters, "visionRangeRva");
        ParseRva(parameters, "maxRangeRva");
        PatchMetadata(log);
        _active = true;
        log.Msg("HOOK OK FogOfWarUnit.CalculateVisionRangeForTarget");
    }

    public static void AdvanceFrame()
    {
        if (!_active)
            return;
        var delta = DeltaTime();
        if (delta <= 0f || delta > 5f)
            return;
        lock (Gate)
            _now += delta;
    }

    static void ReadParameters(JsonElement parameters)
    {
        _cap = ReadNumber(parameters, "capRaw", 1, 100000);
        _exceptionalCap = ReadNumber(parameters, "exceptionalCapRaw", _cap, 100000);
        _exceptionalOptics = ReadNumber(parameters, "exceptionalOptics", 1, 100000);
        _forestCover = ReadNumber(parameters, "forestCover", 1, 100);
        _buildingCover = ReadNumber(parameters, "buildingCover", 1, 100);
        ReadNumber(parameters, "bocageCover", 1, 100);
        _windowSeconds = ReadNumber(parameters, "windowSeconds", 0.01, 600);
        _spottedPenalty = ReadNumber(parameters, "spottedPenalty", 1, 100);
        _trace = ReadBool(parameters, "log");
        _expectedHash = ReadString(parameters, "gameAssemblySha256").Trim().ToLowerInvariant();
        if (_expectedHash.Length != 64)
            throw new InvalidDataException("gameAssemblySha256 must be 64 hex characters");
        var ids = ReadInts(parameters, "weaponId");
        var noise = ReadFloats(parameters, "noise");
        var vehicle = ReadFloats(parameters, "vehicleNoise");
        if (ids.Length != noise.Length || ids.Length != vehicle.Length)
            throw new InvalidDataException("weaponId, noise, and vehicleNoise must have equal length");
        Weapons.Clear();
        for (var i = 0; i < ids.Length; i++)
        {
            if (ids[i] <= 0)
                throw new InvalidDataException("weaponId must be positive");
            if (noise[i] <= 0f || vehicle[i] <= 0f)
                throw new InvalidDataException("noise factors must be positive");
            if (!Weapons.TryAdd(ids[i], (noise[i], vehicle[i])))
                throw new InvalidDataException("weaponId " + ids[i] + " is repeated");
        }
    }

    static string _expectedHash = ExpectedHash;

    static void PatchMetadata(MelonLogger.Instance log)
    {
        var unit = FindType(
            "Il2CppBrokenArrow.Client.Ecs.FogOfWar.FogOfWarUnit",
            "BrokenArrow.Client.Ecs.FogOfWar.FogOfWarUnit");
        var shooting = FindType(
            "Il2CppBrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem",
            "BrokenArrow.Client.Ecs.BattleSystem.Systems.ShootingSystem");
        if (unit == null || shooting == null)
            throw new MissingMethodException("FogOfWarUnit or ShootingSystem");
        _entityType = EntityType(unit);
        var vision = AccessTools.Method(unit, "CalculateVisionRangeForTarget");
        var scan = AccessTools.Method(unit, ScanMethod);
        var fire = AccessTools.Method(shooting, "WeaponForceFire");
        if (vision == null || scan == null || fire == null)
            throw new MissingMethodException("a spotting method is missing");
        var harmony = new HarmonyLib.Harmony("freedomarrow.gameplay.spotting");
        harmony.Patch(vision, postfix: new HarmonyMethod(BindVision(vision)));
        harmony.Patch(scan, postfix: new HarmonyMethod(BindScan(scan)));
        harmony.Patch(fire, postfix: new HarmonyMethod(BindShot(fire)));
        PrepareTypes();
        log.Msg("HOOK OK spotting metadata copies");
    }

    static void PrepareTypes()
    {
        EnsureFog();
        EnsureTerrain();
        EnsureSneak();
        EnsureLabel();
        EnsureParent();
        EnsureWeaponFields();
        _ = Smoke();
        _ = Helicopter();
        _ = Aircraft();
        _ = InfantryType();
    }

    static Type EntityType(Type unit)
    {
        var vision = AccessTools.Method(unit, "CalculateVisionRangeForTarget")
            ?? throw new MissingMethodException("CalculateVisionRangeForTarget");
        var parameter = vision.GetParameters().FirstOrDefault()
            ?? throw new MissingMethodException("CalculateVisionRangeForTarget has no entity");
        var type = parameter.ParameterType;
        if (type.IsByRef)
            type = type.GetElementType() ?? type;
        return type;
    }

    public static void ApplyVision(object? checker, object? target, ref float result)
    {
        if (Interlocked.Increment(ref _visionHarmonyCalls) == 1)
            _log?.Msg("spotting vision metadata hook invoked");
        if (_depth > 0)
            return;
        _depth++;
        try
        {
            result = Compute(checker, target, result);
        }
        catch (Exception ex)
        {
            FailOnce(ex);
        }
        finally
        {
            _depth--;
        }
    }

    public static void ApplyScan(object? checker, ref float maxOpticsRange)
    {
        if (Interlocked.Increment(ref _scanHarmonyCalls) == 1)
            _log?.Msg("spotting scan metadata hook invoked");
        if (_depth > 0 || checker == null)
            return;
        _depth++;
        try
        {
            var raised = Raise(checker, maxOpticsRange);
            if (raised > maxOpticsRange)
                maxOpticsRange = raised;
        }
        catch (Exception ex)
        {
            FailOnce(ex);
        }
        finally
        {
            _depth--;
        }
    }

    public static void RecordShot(object? weapon, object? projectile)
    {
        if (Interlocked.Increment(ref _shotCalls) == 1)
            _log?.Msg("spotting shot hook invoked");
        if (weapon == null || projectile == null || !IsReal(projectile))
            return;
        try
        {
            var parent = ParentUnit(weapon);
            if (parent == null || !IsReal(parent))
                return;
            var info = WeaponObject(weapon);
            if (info == IntPtr.Zero)
                return;
            var id = ReadInt(info, WeaponIdOffset());
            var flash = ReadFloat(info, WeaponFlashOffset());
            var factor = FactorFor(id, flash, Has(parent, InfantryType()));
            if (factor < 1f)
                factor = 1f;
            var key = Key(parent);
            lock (Gate)
            {
                if (!Signatures.TryGetValue(key, out var list))
                {
                    list = new List<Signature>();
                    Signatures[key] = list;
                }
                var expiry = _now + _windowSeconds;
                var refreshed = false;
                foreach (var signature in list)
                {
                    if (signature.WeaponId != id)
                        continue;
                    signature.Factor = factor;
                    signature.Expiry = expiry;
                    refreshed = true;
                    break;
                }
                if (!refreshed)
                    list.Add(new Signature(id, factor, expiry));
                Dirty.Add(key);
            }
        }
        catch (Exception ex)
        {
            FailOnce(ex);
        }
    }

    static float Compute(object? checker, object? target, float native)
    {
        if (checker == null || target == null)
            return native;
        if (IsAir(checker) || IsAir(target))
            return Trace(native, native, "air");
        if (!TryFog(checker, out var optics, out _, out _, out _))
            return native;
        if (optics <= 0f)
            return Trace(native, native, "no-ground-optics");
        if (Has(target, Smoke()))
            return Trace(native, native, "smoke");
        if (!TryFog(target, out _, out var anti, out var flash, out var penalty))
            return native;
        if (Sneaking(target, flash))
            return Trace(native, native, "sneak");
        if (CriticalOptics(checker))
            return Trace(native, native, "critical-optics");
        var cover = Cover(target);
        var noise = Noise(target);
        var spotted = penalty > 0f ? _spottedPenalty : 0f;
        var effective = Math.Max(noise, spotted);
        var raw = optics * anti * effective / cover;
        var cap = CapFor(optics);
        if (raw > cap)
            raw = cap;
        if (raw < 0f)
            raw = 0f;
        NoteChange(target, effective);
        return Trace(native, raw, "ground");
    }

    static float Raise(object checker, float current)
    {
        if (IsAir(checker))
            return current;
        if (!TryFog(checker, out var optics, out _, out _, out _) || optics <= 0f)
            return current;
        var cap = CapFor(optics);
        return cap > current ? cap : current;
    }

    static float CapFor(float optics)
    {
        return Math.Abs(optics - _exceptionalOptics) < 0.5f ? _exceptionalCap : _cap;
    }

    static float Cover(object target)
    {
        if (!Has(target, Terrain()))
            return 1f;
        EnsureTerrain();
        var value = ReadByte(target, Terrain(), _terrainValue);
        if (value == 2)
            return _forestCover;
        if (value == 3)
            return _buildingCover;
        return 1f;
    }

    static bool Sneaking(object target, float flash)
    {
        if (flash > 1f || !Has(target, Sneak()))
            return false;
        EnsureSneak();
        return ReadByte(target, Sneak(), _sneakEnabled) != 0;
    }

    static bool CriticalOptics(object checker)
    {
        if (!Has(checker, Label()))
            return false;
        EnsureLabel();
        return ReadByte(checker, Label(), _labelCrit) != 0;
    }

    static bool IsAir(object entity)
    {
        return Has(entity, Helicopter()) || Has(entity, Aircraft());
    }

    static float Noise(object target)
    {
        if (!IsReal(target))
            return 1f;
        var key = Key(target);
        lock (Gate)
        {
            if (!Signatures.TryGetValue(key, out var list))
                return 1f;
            var best = 1f;
            for (var i = list.Count - 1; i >= 0; i--)
            {
                if (list[i].Expiry <= _now)
                {
                    list.RemoveAt(i);
                    continue;
                }
                if (list[i].Factor > best)
                    best = list[i].Factor;
            }
            if (list.Count == 0)
                Signatures.Remove(key);
            return best;
        }
    }

    static void NoteChange(object target, float effective)
    {
        if (!IsReal(target))
            return;
        var key = Key(target);
        var changed = false;
        lock (Gate)
        {
            if (Dirty.Remove(key))
                changed = true;
            if (!LastEffective.TryGetValue(key, out var previous))
                LastEffective[key] = effective;
            else if (previous != effective)
            {
                LastEffective[key] = effective;
                changed = true;
            }
        }
        if (!changed)
            return;
        try
        {
            EnsureFog();
            WriteByte(target, Fog(), _fogUpdate, 1);
        }
        catch (Exception ex)
        {
            FailOnce(ex);
        }
    }

    static float FactorFor(int id, float flash, bool infantry)
    {
        if (Weapons.TryGetValue(id, out var pair))
            return infantry ? pair.Noise : pair.Vehicle;
        var factor = 1f + flash;
        return factor < 1f ? 1f : factor;
    }

    static object? ParentUnit(object weapon)
    {
        if (!Has(weapon, Parent()))
            return null;
        EnsureParent();
        var root = ReadEntity(weapon, Parent(), _parentRoot);
        if (IsReal(root))
            return root;
        return ReadEntity(weapon, Parent(), _parentValue);
    }

    static IntPtr WeaponObject(object weapon)
    {
        if (!Has(weapon, Weapon()))
            return IntPtr.Zero;
        var slot = GetPtr(weapon, Weapon());
        if (slot == IntPtr.Zero)
            return IntPtr.Zero;
        EnsureWeaponFields();
        if (_weaponPointerMode == 2)
            return LooksLikeWeapon(slot) ? slot : IntPtr.Zero;
        if (_weaponPointerMode == 1)
        {
            var nested = Marshal.ReadIntPtr(slot);
            return LooksLikeWeapon(nested) ? nested : IntPtr.Zero;
        }
        if (LooksLikeWeapon(slot))
        {
            _weaponPointerMode = 2;
            return slot;
        }
        var dereferenced = Marshal.ReadIntPtr(slot);
        if (LooksLikeWeapon(dereferenced))
        {
            _weaponPointerMode = 1;
            return dereferenced;
        }
        return IntPtr.Zero;
    }

    static bool LooksLikeWeapon(IntPtr pointer)
    {
        if (pointer == IntPtr.Zero)
            return false;
        try
        {
            var id = ReadInt(pointer, WeaponIdOffset());
            var flash = ReadFloat(pointer, WeaponFlashOffset());
            return id > 0 && id < 100000 && flash >= 0f && flash <= 20f;
        }
        catch
        {
            return false;
        }
    }

    static bool TryFog(object entity, out float distance, out float anti, out float flash, out float penalty)
    {
        distance = anti = flash = penalty = 0f;
        if (!Has(entity, Fog()))
            return false;
        EnsureFog();
        distance = ReadFloat(entity, Fog(), _fogDistance);
        anti = ReadFloat(entity, Fog(), _fogAnti);
        flash = ReadFloat(entity, Fog(), _fogFlash);
        penalty = ReadFloat(entity, Fog(), _fogPenalty);
        return true;
    }

    static float Trace(float before, float after, string reason)
    {
        if (!_trace || reason != "ground")
            return after;
        var count = Interlocked.Increment(ref _loggedRanges);
        if (count <= 20 || count % 200 == 0)
            _log?.Msg($"spotting {reason} {before} -> {after}");
        return after;
    }

    static void FailOnce(Exception ex)
    {
        if (_failed)
            return;
        _failed = true;
        _log?.Error("spotting hook error: " + ex.Message);
    }

    static float DeltaTime()
    {
        _deltaTime ??= FindType("UnityEngine.Time")?.GetProperty("deltaTime", BindingFlags.Public | BindingFlags.Static);
        if (_deltaTime == null)
            return 0f;
        var value = _deltaTime.GetValue(null);
        return value == null ? 0f : Convert.ToSingle(value);
    }

    static object Box(IntPtr native)
    {
        if (_entityType == null)
            throw new InvalidOperationException("spotting has no Entity type");
        var box = Activator.CreateInstance(_entityType)!;
        var handle = GCHandle.Alloc(box, GCHandleType.Pinned);
        try
        {
            unsafe
            {
                Buffer.MemoryCopy((void*)native, (void*)handle.AddrOfPinnedObject(), 8, 8);
            }
        }
        finally
        {
            handle.Free();
        }
        return box;
    }

    static bool IsReal(object entity)
    {
        var (version, world, id) = Parts(entity);
        return version != 0 || world != 0 || id != 0;
    }

    static long Key(object entity)
    {
        var (version, world, id) = Parts(entity);
        return ((long)(ushort)version << 48) | ((long)(ushort)world << 32) | (uint)id;
    }

    static (short Version, short World, int Id) Parts(object entity)
    {
        var handle = GCHandle.Alloc(entity, GCHandleType.Pinned);
        try
        {
            unsafe
            {
                var pointer = (byte*)handle.AddrOfPinnedObject();
                return (*(short*)pointer, *(short*)(pointer + 2), *(int*)(pointer + 4));
            }
        }
        finally
        {
            handle.Free();
        }
    }

    static ProcessModule FindModule()
    {
        foreach (ProcessModule module in Process.GetCurrentProcess().Modules)
        {
            if (string.Equals(module.ModuleName, "GameAssembly.dll", StringComparison.OrdinalIgnoreCase))
                return module;
        }
        throw new FileNotFoundException("GameAssembly.dll is not loaded");
    }

    static string Hash(string path)
    {
        using var stream = File.OpenRead(path);
        using var sha = SHA256.Create();
        return Convert.ToHexString(sha.ComputeHash(stream)).ToLowerInvariant();
    }

    static long ParseRva(JsonElement parameters, string name)
    {
        var text = ReadString(parameters, name).Trim();
        if (text.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
            text = text[2..];
        if (!long.TryParse(text, System.Globalization.NumberStyles.HexNumber, null, out var value) || value <= 0)
            throw new InvalidDataException(name + " must be a hex RVA");
        return value;
    }

    static float ReadNumber(JsonElement parameters, string name, double min, double max)
    {
        if (!parameters.TryGetProperty(name, out var property) || property.ValueKind != JsonValueKind.Number)
            throw new InvalidDataException(name + " must be a number");
        var value = property.GetDouble();
        if (value < min || value > max)
            throw new InvalidDataException(name + " is outside " + min + " to " + max);
        return (float)value;
    }

    static bool ReadBool(JsonElement parameters, string name)
    {
        if (!parameters.TryGetProperty(name, out var property)
            || property.ValueKind is not (JsonValueKind.True or JsonValueKind.False))
            throw new InvalidDataException(name + " must be a boolean");
        return property.GetBoolean();
    }

    static string ReadString(JsonElement parameters, string name)
    {
        if (!parameters.TryGetProperty(name, out var property) || property.ValueKind != JsonValueKind.String)
            throw new InvalidDataException(name + " must be a string");
        var text = property.GetString();
        if (string.IsNullOrWhiteSpace(text))
            throw new InvalidDataException(name + " must be a non-empty string");
        return text;
    }

    static int[] ReadInts(JsonElement parameters, string name)
    {
        var array = ReadArray(parameters, name);
        var values = new int[array.GetArrayLength()];
        var index = 0;
        foreach (var item in array.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Number || !item.TryGetInt32(out values[index]))
                throw new InvalidDataException(name + " must be an array of integers");
            index++;
        }
        return values;
    }

    static float[] ReadFloats(JsonElement parameters, string name)
    {
        var array = ReadArray(parameters, name);
        var values = new float[array.GetArrayLength()];
        var index = 0;
        foreach (var item in array.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Number)
                throw new InvalidDataException(name + " must be an array of numbers");
            values[index] = (float)item.GetDouble();
            index++;
        }
        return values;
    }

    static JsonElement ReadArray(JsonElement parameters, string name)
    {
        if (!parameters.TryGetProperty(name, out var property) || property.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException(name + " must be an array");
        return property;
    }

    static MethodInfo BindVision(MethodInfo target)
    {
        var parameters = target.GetParameters();
        var checker = IndexOf(parameters, "checkerEntity", 0);
        var other = IndexOf(parameters, "target", 1);
        var types = parameters.Select(parameter => parameter.ParameterType).Append(typeof(float).MakeByRefType()).ToArray();
        var (type, method) = Define("VisionPost", typeof(void), types, parameters, resultName: "__result");
        var il = method.GetILGenerator();
        EmitArg(il, checker, parameters[checker].ParameterType);
        EmitArg(il, other, parameters[other].ParameterType);
        il.Emit(OpCodes.Ldarg, parameters.Length);
        il.Emit(OpCodes.Call, typeof(GroundSpotting).GetMethod(nameof(ApplyVision))!);
        il.Emit(OpCodes.Ret);
        return type.CreateType()!.GetMethod("Post")!;
    }

    static MethodInfo BindScan(MethodInfo target)
    {
        var parameters = target.GetParameters();
        var checker = IndexOf(parameters, "checker", 0);
        var optics = IndexOf(parameters, "maxOpticsRange", 1);
        var types = parameters.Select(parameter => parameter.ParameterType).ToArray();
        var (type, method) = Define("ScanPost", typeof(void), types, parameters, resultName: null);
        var il = method.GetILGenerator();
        EmitArg(il, checker, parameters[checker].ParameterType);
        il.Emit(OpCodes.Ldarg, optics);
        il.Emit(OpCodes.Call, typeof(GroundSpotting).GetMethod(nameof(ApplyScan))!);
        il.Emit(OpCodes.Ret);
        return type.CreateType()!.GetMethod("Post")!;
    }

    static MethodInfo BindShot(MethodInfo target)
    {
        var parameters = target.GetParameters();
        var weapon = IndexOf(parameters, "weaponEntity", 0);
        var projectile = IndexOf(parameters, "projectile", 1);
        var types = new[] { parameters[weapon].ParameterType, parameters[projectile].ParameterType };
        var chosen = new[] { parameters[weapon], parameters[projectile] };
        var (type, method) = Define("ShotPost", typeof(void), types, chosen, resultName: null);
        var il = method.GetILGenerator();
        EmitArg(il, 0, types[0]);
        EmitArg(il, 1, types[1]);
        il.Emit(OpCodes.Call, typeof(GroundSpotting).GetMethod(nameof(RecordShot))!);
        il.Emit(OpCodes.Ret);
        return type.CreateType()!.GetMethod("Post")!;
    }

    static (TypeBuilder Type, MethodBuilder Method) Define(string name, Type returnType, Type[] types, ParameterInfo[] source, string? resultName)
    {
        var assembly = AssemblyBuilder.DefineDynamicAssembly(new AssemblyName("FreedomArrow" + name), AssemblyBuilderAccess.Run);
        var module = assembly.DefineDynamicModule(name);
        var type = module.DefineType(name, TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed);
        var method = type.DefineMethod("Post", MethodAttributes.Public | MethodAttributes.Static, returnType, types);
        for (var i = 0; i < source.Length && i < types.Length; i++)
        {
            var parameterName = string.IsNullOrEmpty(source[i].Name) ? "p" + i : source[i].Name;
            method.DefineParameter(i + 1, ParameterAttributes.None, parameterName);
        }
        if (resultName != null)
            method.DefineParameter(types.Length, ParameterAttributes.None, resultName);
        return (type, method);
    }

    static int IndexOf(ParameterInfo[] parameters, string name, int fallback)
    {
        for (var i = 0; i < parameters.Length; i++)
        {
            if (parameters[i].Name == name)
                return i;
        }
        return fallback < parameters.Length ? fallback : 0;
    }

    static void EmitArg(ILGenerator il, int index, Type type)
    {
        il.Emit(OpCodes.Ldarg, index);
        if (!type.IsByRef)
        {
            if (type.IsValueType)
                il.Emit(OpCodes.Box, type);
            return;
        }
        var element = type.GetElementType() ?? type;
        if (element == typeof(float))
            return;
        il.Emit(OpCodes.Ldobj, element);
        if (element.IsValueType)
            il.Emit(OpCodes.Box, element);
    }

    static void EnsureFog()
    {
        if (_fogDistance != int.MinValue)
            return;
        var type = Fog();
        _fogDistance = FieldOffset(type, "DistanceGround");
        _fogAnti = FieldOffset(type, "AntiVisible");
        _fogFlash = FieldOffset(type, "WeaponFlash");
        _fogPenalty = FieldOffset(type, "SpottedPenalty");
        _fogUpdate = FieldOffset(type, "UpdateRequired");
    }

    static void EnsureTerrain()
    {
        if (_terrainValue == int.MinValue)
            _terrainValue = FieldOffset(Terrain(), "Value");
    }

    static void EnsureSneak()
    {
        if (_sneakEnabled == int.MinValue)
            _sneakEnabled = FieldOffset(Sneak(), "IsEnabled");
    }

    static void EnsureLabel()
    {
        if (_labelCrit == int.MinValue)
            _labelCrit = FieldOffset(Label(), "CritLevelOptics");
    }

    static void EnsureParent()
    {
        if (_parentRoot != int.MinValue)
            return;
        var type = Parent();
        _parentRoot = FieldOffset(type, "Root");
        _parentValue = FieldOffset(type, "Value");
    }

    static void EnsureWeaponFields()
    {
        if (_weaponInfo != int.MinValue)
            return;
        _weaponInfo = RawOffset(Weapon(), "WeaponInfo");
        var weapons = FindType(
            "Il2CppBrokenArrow.DataBase.Models.Weapons",
            "BrokenArrow.DataBase.Models.Weapons");
        if (weapons == null)
            throw new MissingFieldException("Weapons");
        _weaponId = RawOffset(weapons, "<Id>k__BackingField");
        if (_weaponId < 0)
            _weaponId = RawOffset(weapons, "Id");
        _weaponFlash = RawOffset(weapons, "<FlashPerShot>k__BackingField");
        if (_weaponFlash < 0)
            _weaponFlash = RawOffset(weapons, "FlashPerShot");
        if (_weaponInfo < 0 || _weaponId < 0 || _weaponFlash < 0)
            throw new MissingFieldException("weapon id or FlashPerShot");
    }

    static int WeaponIdOffset()
    {
        EnsureWeaponFields();
        return _weaponId;
    }

    static int WeaponFlashOffset()
    {
        EnsureWeaponFields();
        return _weaponFlash;
    }

    static Type Fog() => _fogType ??= Required(
        "Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components.FogOfWarComponent",
        "BrokenArrow.Client.Ecs.FogOfWar.Components.FogOfWarComponent");

    static Type Terrain() => _terrainType ??= Required(
        "Il2CppBrokenArrow.Shared.Ecs.Components.Movement.TerrainTypeComponent",
        "BrokenArrow.Shared.Ecs.Components.Movement.TerrainTypeComponent");

    static Type Sneak() => _sneakType ??= Required(
        "Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components.SneakAbilityComponent",
        "BrokenArrow.Client.Ecs.FogOfWar.Components.SneakAbilityComponent");

    static Type Smoke() => _smokeType ??= Required(
        "Il2CppBrokenArrow.Client.Ecs.FogOfWar.Components.UnitInsideSmokeComponent",
        "BrokenArrow.Client.Ecs.FogOfWar.Components.UnitInsideSmokeComponent");

    static Type Helicopter() => _helicopterType ??= Required(
        "Il2CppBrokenArrow.Shared.Ecs.Components.UnitHelicopterFlag",
        "BrokenArrow.Shared.Ecs.Components.UnitHelicopterFlag");

    static Type Aircraft() => _aircraftType ??= Required(
        "Il2CppBrokenArrow.Shared.Ecs.Components.UnitAircraftComponent",
        "BrokenArrow.Shared.Ecs.Components.UnitAircraftComponent");

    static Type InfantryType() => _infantryType ??= Required(
        "Il2CppBrokenArrow.Shared.Ecs.Components.UnitInfantryFlag",
        "BrokenArrow.Shared.Ecs.Components.UnitInfantryFlag");

    static Type Label() => _labelType ??= Required(
        "Il2CppBrokenArrow.Client.Ecs.UI.Labels.Components.LabelDataComponent",
        "BrokenArrow.Client.Ecs.UI.Labels.Components.LabelDataComponent");

    static Type Parent() => _parentType ??= Required(
        "Il2CppBrokenArrow.Shared.Ecs.Components.ParentComponent",
        "BrokenArrow.Shared.Ecs.Components.ParentComponent");

    static Type Weapon() => _weaponType ??= Required(
        "Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components.WeaponComponent",
        "BrokenArrow.Client.Ecs.BattleSystem.Components.WeaponComponent");

    static Type Required(params string[] names)
    {
        return FindType(names) ?? throw new TypeLoadException(names[0]);
    }

    static bool Has(object entity, Type component)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(HasTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (bool)method.MakeGenericMethod(entity.GetType()).Invoke(null, new[] { entity, component })!;
    }

    static float ReadFloat(object entity, Type component, int offset)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(ReadFloatTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (float)method.MakeGenericMethod(entity.GetType()).Invoke(null, new object[] { entity, component, offset })!;
    }

    static byte ReadByte(object entity, Type component, int offset)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(ReadByteTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (byte)method.MakeGenericMethod(entity.GetType()).Invoke(null, new object[] { entity, component, offset })!;
    }

    static void WriteByte(object entity, Type component, int offset, byte value)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(WriteByteTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        method.MakeGenericMethod(entity.GetType()).Invoke(null, new object[] { entity, component, offset, value });
    }

    static object ReadEntity(object entity, Type component, int offset)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(ReadEntityTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return method.MakeGenericMethod(entity.GetType()).Invoke(null, new object[] { entity, component, offset })!;
    }

    static IntPtr GetPtr(object entity, Type component)
    {
        var method = typeof(GroundSpotting).GetMethod(nameof(GetPtrTyped), BindingFlags.NonPublic | BindingFlags.Static)!;
        return (IntPtr)method.MakeGenericMethod(entity.GetType()).Invoke(null, new[] { entity, component })!;
    }

    static bool HasTyped<T>(object boxed, Type component) where T : struct
    {
        var entity = (T)boxed;
        return HasNative(ref entity, component);
    }

    static float ReadFloatTyped<T>(object boxed, Type component, int offset) where T : struct
    {
        var entity = (T)boxed;
        unsafe
        {
            return *(float*)((byte*)GetNative(ref entity, component) + offset);
        }
    }

    static byte ReadByteTyped<T>(object boxed, Type component, int offset) where T : struct
    {
        var entity = (T)boxed;
        unsafe
        {
            return *((byte*)GetNative(ref entity, component) + offset);
        }
    }

    static void WriteByteTyped<T>(object boxed, Type component, int offset, byte value) where T : struct
    {
        var entity = (T)boxed;
        unsafe
        {
            *((byte*)GetNative(ref entity, component) + offset) = value;
        }
    }

    static object ReadEntityTyped<T>(object boxed, Type component, int offset) where T : struct
    {
        var entity = (T)boxed;
        unsafe
        {
            return Box((IntPtr)((byte*)GetNative(ref entity, component) + offset));
        }
    }

    static IntPtr GetPtrTyped<T>(object boxed, Type component) where T : struct
    {
        var entity = (T)boxed;
        return GetNative(ref entity, component);
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

    unsafe static IntPtr GetNative<T>(ref T entity, Type component) where T : struct
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
        var raw = RawOffset(component, name);
        if (raw < 0)
            throw new MissingFieldException(component.Name + "." + name);
        return raw - 2 * IntPtr.Size;
    }

    static int RawOffset(Type component, string name)
    {
        var store = typeof(Il2CppClassPointerStore<>).MakeGenericType(component);
        var klass = (IntPtr)store.GetField("NativeClassPtr")!.GetValue(null)!;
        var field = IL2CPP.il2cpp_class_get_field_from_name(klass, name);
        if (field == IntPtr.Zero)
            return -1;
        return (int)IL2CPP.il2cpp_field_get_offset(field);
    }

    static int ReadInt(IntPtr pointer, int offset)
    {
        return Marshal.ReadInt32(pointer, offset);
    }

    static float ReadFloat(IntPtr pointer, int offset)
    {
        var bits = Marshal.ReadInt32(pointer, offset);
        return BitConverter.Int32BitsToSingle(bits);
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
