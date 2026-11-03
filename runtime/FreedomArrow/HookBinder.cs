using System.Reflection;
using System.Reflection.Emit;

namespace FreedomArrow;

static class HookBinder
{
    public static MethodInfo Prefix(string parameterName, Type parameterType, string bodyName)
    {
        var assembly = AssemblyBuilder.DefineDynamicAssembly(new AssemblyName("FreedomArrowHooks"), AssemblyBuilderAccess.Run);
        var module = assembly.DefineDynamicModule("hooks");
        var type = module.DefineType("CompiledPrefix", TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed);
        var method = type.DefineMethod("Prefix", MethodAttributes.Public | MethodAttributes.Static, typeof(void), new[] { parameterType });
        method.DefineParameter(1, ParameterAttributes.None, parameterName);
        var il = method.GetILGenerator();
        il.Emit(OpCodes.Ldarg_0);
        if (parameterType.IsValueType)
            il.Emit(OpCodes.Box, parameterType);
        var body = typeof(DatabaseMerge).GetMethod(bodyName, BindingFlags.Public | BindingFlags.Static)
            ?? throw new MissingMethodException(bodyName);
        il.Emit(OpCodes.Call, body);
        il.Emit(OpCodes.Ret);
        return type.CreateType()!.GetMethod("Prefix")!;
    }

    public static MethodInfo Postfix(MethodInfo target, MethodInfo body)
    {
        var parameters = target.GetParameters();
        var types = parameters.Select(parameter => parameter.ParameterType).Append(typeof(float).MakeByRefType()).ToArray();
        var assembly = AssemblyBuilder.DefineDynamicAssembly(new AssemblyName("FreedomArrowPost"), AssemblyBuilderAccess.Run);
        var module = assembly.DefineDynamicModule("post");
        var type = module.DefineType("HitPost", TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed);
        var method = type.DefineMethod("Post", MethodAttributes.Public | MethodAttributes.Static, typeof(void), types);
        for (var i = 0; i < parameters.Length; i++)
        {
            var name = string.IsNullOrEmpty(parameters[i].Name) ? "__" + i : parameters[i].Name;
            method.DefineParameter(i + 1, ParameterAttributes.None, name);
        }
        method.DefineParameter(parameters.Length + 1, ParameterAttributes.None, "__result");
        var il = method.GetILGenerator();
        var targetIndex = IndexOf(parameters, "target", 0);
        var ammoIndex = IndexOf(parameters, "ammoInfo", 2);
        EmitArg(il, targetIndex, parameters[targetIndex].ParameterType);
        EmitArg(il, ammoIndex, parameters[ammoIndex].ParameterType);
        il.Emit(OpCodes.Ldarg, parameters.Length);
        il.Emit(OpCodes.Call, body);
        il.Emit(OpCodes.Ret);
        return type.CreateType()!.GetMethod("Post")!;
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
        if (type.IsValueType)
            il.Emit(OpCodes.Box, type);
    }
}
