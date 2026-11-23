using System.Text.Json;
using System.Text.Json.Serialization;
namespace FreedomArrow;
// Engine diagnostics can contain non-finite sentinels. Preserve their meaning as
// valid JSON strings, rather than fabricating zero or stopping the observer.
static class AaLogJson
{
    static readonly JsonSerializerOptions Options=new(){NumberHandling=JsonNumberHandling.AllowNamedFloatingPointLiterals};
    public static string Serialize<T>(T value)=>JsonSerializer.Serialize(value,Options);
}
