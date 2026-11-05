using System.Text.Json.Nodes;
namespace FreedomArrow;
public sealed class DetectionSettings
{
    public float MaxFlashValue{get;}
    public float SpottedPenalty{get;}
    public float SpottedPenaltyBuildings{get;}
    public float ForestCover{get;}
    public float BuildingCover{get;}
    public DetectionSettings(float flash,float spotted,float spottedBuildings,float forest,float building)
    {
        MaxFlashValue=flash;SpottedPenalty=spotted;SpottedPenaltyBuildings=spottedBuildings;ForestCover=forest;BuildingCover=building;
    }
    public static DetectionSettings Parse(string json)
    {
        var o=JsonNode.Parse(json).AsObject();
        float Read(string name,float min,float max)
        {
            if(!o.TryGetPropertyValue(name,out var node)||node==null)throw new InvalidDataException("Missing detection setting "+name);
            float v=node.GetValue<float>();
            if(!(v>=min&&v<=max))throw new InvalidDataException("Detection setting out of range: "+name);
            return v;
        }
        if(o.Count!=5)throw new InvalidDataException("Unexpected detection settings");
        return new(Read("MaxFlashValue",1,10),Read("SpottedPenalty",1,10),Read("SpottedPenaltyBuildings",1,10),Read("ForestCover",1,10),Read("BuildingCover",1,10));
    }
}
