using System.Text.Json.Nodes;
namespace FreedomArrow;

// Shared by the live loader and launch-free regression checks.
public static class RowPlanner
{
    public static JsonArray Apply(JsonArray source, JsonObject patches, bool allowNew, Action<string,string,JsonNode,JsonNode,bool> receipt)
    {
        var rows=JsonNode.Parse(source.ToJsonString()).AsArray();
        var index=new Dictionary<string,JsonObject>();
        foreach(var item in rows)
        {
            var row=item.AsObject();string id=row["Id"].ToJsonString();
            if(!index.TryAdd(id,row))throw new InvalidDataException("Duplicate row "+id);
        }
        foreach(var patch in patches)
        {
            if(!int.TryParse(patch.Key,out int id)||id<=0||id.ToString()!=patch.Key)
                throw new InvalidDataException("Invalid canonical Int32 row "+patch.Key);
            if(patch.Value==null)
            {
                // A null patch deletes the row. Row references are checked when the package is built.
                if(!index.Remove(patch.Key,out var gone))throw new InvalidDataException("Missing row to delete "+patch.Key);
                rows.Remove(gone);
                receipt(patch.Key,"(row)",null,null,false);
                continue;
            }
            var fields=patch.Value.AsObject();
            bool added=!index.TryGetValue(patch.Key,out var row);
            if(added)
            {
                if(!allowNew||source.Count==0)throw new InvalidDataException("Missing row "+patch.Key);
                var template=source[0].AsObject();
                if(fields.ContainsKey("Id")||!fields.Select(x=>x.Key).ToHashSet().SetEquals(template.Select(x=>x.Key).Where(k=>k!="Id")))
                    throw new InvalidDataException("New row must supply every non-Id field: "+patch.Key);
                row=new JsonObject{["Id"]=id};
            }
            foreach(var field in fields)
            {
                if(field.Key=="Id"||(!added&&!row.ContainsKey(field.Key)))throw new InvalidDataException("Unknown/immutable field "+field.Key);
                bool compatible=added
                    ?source.Any(r=>r.AsObject().ContainsKey(field.Key)&&JsonTypes.Kind(r[field.Key])==JsonTypes.Kind(field.Value))
                    :JsonTypes.Kind(row[field.Key])==JsonTypes.Kind(field.Value);
                if(!compatible)throw new InvalidDataException("Field type mismatch "+field.Key);
                JsonNode before=added?null:Clone(row[field.Key]);
                row[field.Key]=Clone(field.Value);
                receipt(patch.Key,field.Key,before,Clone(field.Value),added);
            }
            if(added){rows.Add(row);index.Add(patch.Key,row);}
        }
        return rows;
    }
    static JsonNode Clone(JsonNode n)=>n==null?null:JsonNode.Parse(n.ToJsonString());
}
