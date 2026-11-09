using System.Reflection;
using System.Runtime.CompilerServices;
using Il2CppDefaultEcs;
using Il2CppInterop.Runtime;
using Il2CppInterop.Runtime.InteropTypes;
using Il2CppInterop.Runtime.Runtime;
using Il2CppBrokenArrow.Client.Ecs.BattleSystem.Components;

namespace FreedomArrow;

// Entity.Get<T> returns native unboxed storage. Generated reference-return wrappers
// cannot represent that storage as an Il2CppObjectBase. Box a READ SNAPSHOT instead.
// Reference fields stay owned by IL2CPP; a strong handle roots each snapshot until
// its managed proxy is collected. Never write a snapshot expecting live mutation.
internal static unsafe class NativeEcs
{
    sealed class Root
    {
        IntPtr handle;
        public Root(IntPtr value) { handle = IL2CPP.il2cpp_gchandle_new(value, false); }
        public void Release() { var old=Interlocked.Exchange(ref handle,IntPtr.Zero); if(old!=IntPtr.Zero&&!Environment.HasShutdownStarted)IL2CPP.il2cpp_gchandle_free(old); }
        ~Root() { Release(); }
    }
    static readonly ConditionalWeakTable<Il2CppObjectBase, Root> roots = new();
    static readonly Dictionary<(Type,string),IntPtr> methods = new();
    static IntPtr Method<T>(string operation)
    {
        var key=(typeof(T),operation);
        if(methods.TryGetValue(key,out var result))return result;
        var store=(typeof(Entity).GetNestedType(operation,BindingFlags.Public|BindingFlags.NonPublic)
            ??throw new MissingMemberException(operation)).MakeGenericType(typeof(T));
        RuntimeHelpers.RunClassConstructor(store.TypeHandle);
        result=(IntPtr)(store.GetField("Pointer",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic)?.GetValue(null)
            ??throw new MissingFieldException(operation));
        if(result==IntPtr.Zero)throw new InvalidOperationException("Native ECS generic method unavailable: "+typeof(T).Name);
        return methods[key]=result;
    }
    static IntPtr Class<T>()
    {
        RuntimeHelpers.RunClassConstructor(typeof(T).TypeHandle);
        var c=Il2CppClassPointerStore<T>.NativeClassPtr;
        if(c==IntPtr.Zero)throw new InvalidOperationException("Missing native component type: "+typeof(T).Name);
        return c;
    }
    static IntPtr Data<T>(Entity entity)
    {
        if(!entity.IsAlive||!entity.Has<T>())throw new InvalidOperationException("Missing live component "+typeof(T).Name);
        var method=Method<T>("MethodInfoStoreGeneric_Get_Public_byref_T_0`1");
        var code=*(IntPtr*)method;
        if(code==IntPtr.Zero)throw new InvalidOperationException("Missing compiled component getter");
        var data=((delegate* unmanaged<Entity*,IntPtr,IntPtr>)code)(&entity,method);
        if(data==IntPtr.Zero)throw new InvalidOperationException("Null component storage");
        return data;
    }
    static TValue Unbox<TValue>(IntPtr boxed) where TValue:unmanaged
    {
        if(boxed==IntPtr.Zero)throw new InvalidOperationException("Null native property result");
        var root=new Root(boxed);
        try
        {
            uint align=0;
            if(IL2CPP.il2cpp_class_value_size(IL2CPP.il2cpp_object_get_class(boxed),ref align)!=sizeof(TValue))
                throw new InvalidOperationException("Native property result size mismatch: "+typeof(TValue).Name);
            return Unsafe.ReadUnaligned<TValue>((void*)IL2CPP.il2cpp_object_unbox(boxed));
        }
        finally{root.Release();}
    }
    public static TValue Property<TComponent,TValue>(Entity entity,string property) where TValue:unmanaged
    {
        var c=Class<TComponent>();
        if(!IL2CPP.il2cpp_class_is_valuetype(c))throw new InvalidOperationException("Property reader expects a value component");
        var method=IL2CPP.il2cpp_class_get_method_from_name(c,"get_"+property,0);
        if(method==IntPtr.Zero)throw new MissingMemberException(typeof(TComponent).Name,property);
        IntPtr exception=IntPtr.Zero;
        var result=IL2CPP.il2cpp_runtime_invoke(method,Data<TComponent>(entity),null,ref exception);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(exception);
        return Unbox<TValue>(result);
    }
    public static TValue Field<TComponent,TValue>(Entity entity,string name) where TValue:unmanaged
    {
        var c=Class<TComponent>();
        if(!IL2CPP.il2cpp_class_is_valuetype(c))throw new InvalidOperationException("Field reader expects a value component");
        var field=IL2CPP.il2cpp_class_get_field_from_name(c,name);
        if(field==IntPtr.Zero)throw new MissingFieldException(typeof(TComponent).Name,name);
        uint align=0;var fieldClass=IL2CPP.il2cpp_class_from_type(IL2CPP.il2cpp_field_get_type(field));
        if(IL2CPP.il2cpp_class_value_size(fieldClass,ref align)!=sizeof(TValue))throw new InvalidOperationException("Native field size mismatch: "+name);
        int offset=Offset<TComponent>(name);align=0;
        if(offset+sizeof(TValue)>IL2CPP.il2cpp_class_value_size(c,ref align))throw new InvalidOperationException("Field exceeds native component");
        return Unsafe.ReadUnaligned<TValue>((byte*)Data<TComponent>(entity)+offset);
    }
    // Live write into the component storage that Entity.Get<T> returns (not a snapshot). Same size checks as Field.
    public static void WriteField<TComponent,TValue>(Entity entity,string name,TValue value) where TValue:unmanaged
    {
        var c=Class<TComponent>();
        if(!IL2CPP.il2cpp_class_is_valuetype(c))throw new InvalidOperationException("Field writer expects a value component");
        var field=IL2CPP.il2cpp_class_get_field_from_name(c,name);
        if(field==IntPtr.Zero)throw new MissingFieldException(typeof(TComponent).Name,name);
        uint align=0;var fieldClass=IL2CPP.il2cpp_class_from_type(IL2CPP.il2cpp_field_get_type(field));
        if(IL2CPP.il2cpp_class_value_size(fieldClass,ref align)!=sizeof(TValue))throw new InvalidOperationException("Native field size mismatch: "+name);
        int offset=Offset<TComponent>(name);align=0;
        if(offset+sizeof(TValue)>IL2CPP.il2cpp_class_value_size(c,ref align))throw new InvalidOperationException("Field exceeds native component");
        Unsafe.WriteUnaligned((byte*)Data<TComponent>(entity)+offset,value);
    }
    public static float EncodedField<TComponent>(Entity entity,string name)
    {
        var field=IL2CPP.il2cpp_class_get_field_from_name(Class<TComponent>(),name);
        if(field==IntPtr.Zero)throw new MissingFieldException(typeof(TComponent).Name,name);
        var fieldClass=IL2CPP.il2cpp_class_from_type(IL2CPP.il2cpp_field_get_type(field));
        var method=IL2CPP.il2cpp_class_get_method_from_name(fieldClass,"get_Value",0);
        if(method==IntPtr.Zero)throw new MissingMemberException(name,"Value");
        IntPtr exception=IntPtr.Zero;
        var result=IL2CPP.il2cpp_runtime_invoke(method,(IntPtr)((byte*)Data<TComponent>(entity)+Offset<TComponent>(name)),null,ref exception);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(exception);
        return Unbox<float>(result);
    }
    // Same as EncodedField for a protected int (GAInt/GInt): calls the field's get_Value and unboxes an int.
    public static int EncodedInt<TComponent>(Entity entity,string name)
    {
        var field=IL2CPP.il2cpp_class_get_field_from_name(Class<TComponent>(),name);
        if(field==IntPtr.Zero)throw new MissingFieldException(typeof(TComponent).Name,name);
        var fieldClass=IL2CPP.il2cpp_class_from_type(IL2CPP.il2cpp_field_get_type(field));
        var method=IL2CPP.il2cpp_class_get_method_from_name(fieldClass,"get_Value",0);
        if(method==IntPtr.Zero)throw new MissingMemberException(name,"Value");
        IntPtr exception=IntPtr.Zero;
        var result=IL2CPP.il2cpp_runtime_invoke(method,(IntPtr)((byte*)Data<TComponent>(entity)+Offset<TComponent>(name)),null,ref exception);
        Il2CppInterop.Runtime.Il2CppException.RaiseExceptionIfNecessary(exception);
        return Unbox<int>(result);
    }
    public static T ReadValue<T>(Entity entity) where T:unmanaged
    {
        var c=Class<T>();uint align=0;
        if(!IL2CPP.il2cpp_class_is_valuetype(c)||IL2CPP.il2cpp_class_value_size(c,ref align)!=sizeof(T))
            throw new InvalidOperationException("Managed/native value layout mismatch: "+typeof(T).Name);
        return Unsafe.ReadUnaligned<T>((void*)Data<T>(entity));
    }
    public static T Read<T>(Entity entity) where T:Il2CppObjectBase
    {
        var c=Class<T>();var p=Data<T>(entity);
        // Value components need boxing; class components store an object reference in the returned slot.
        var boxed=IL2CPP.il2cpp_class_is_valuetype(c)?IL2CPP.il2cpp_value_box(c,p):*(IntPtr*)p;
        if(boxed==IntPtr.Zero)throw new InvalidOperationException("Cannot box native component");
        var root=new Root(boxed);
        var proxy=Il2CppObjectPool.Get<T>(boxed);
        if(roots.TryGetValue(proxy,out _))root.Release();else roots.Add(proxy,root);
        return proxy;
    }
    static int Offset<T>(string name)
    {
        var c=Class<T>();uint align=0;int size=IL2CPP.il2cpp_class_value_size(c,ref align);
        var field=IL2CPP.il2cpp_class_get_field_from_name(c,name);
        if(field==IntPtr.Zero)throw new MissingFieldException(typeof(T).Name,name);
        int offset=checked((int)IL2CPP.il2cpp_field_get_offset(field)-2*IntPtr.Size);
        if(offset<0||offset+4>size)throw new InvalidOperationException("Component field outside native layout: "+name);
        return offset;
    }
}
