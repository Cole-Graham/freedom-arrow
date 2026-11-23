using System.Text.Json;
using System.Text.Json.Nodes;
namespace FreedomArrow;
public static class JsonTypes
{
    // JSON true and false are values of one boolean type; ValueKind distinguishes the values.
    public static JsonValueKind Kind(JsonNode node)
    {
        if(node==null)return JsonValueKind.Null;
        var kind=JsonSerializer.SerializeToElement(node).ValueKind;
        return kind==JsonValueKind.False ? JsonValueKind.True : kind;
    }
}
