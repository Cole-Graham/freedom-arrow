using FreedomArrow;
using System.Text.Json;

int checks=0;
void Check(bool ok,string message){checks++;if(!ok)throw new Exception(message);}
Check(ArsenalSpecPolicy.GroupFor(18,new[]{18,19},new[]{19})==19,"HQ-9 / PLZ-05 follow Rocket Force selection");
Check(ArsenalSpecPolicy.GroupFor(17,new[]{17,19,21},new[]{19})==19,"Shared transport follows Rocket Force");
Check(ArsenalSpecPolicy.GroupFor(17,new[]{17,18,19,20,21},new[]{21})==21,"Shared fighter follows Motorized");
Check(ArsenalSpecPolicy.GroupFor(17,new[]{17,19,21},new[]{17,19})==17,"Keep original heading when still selected");
Check(ArsenalSpecPolicy.GroupFor(17,new[]{17,19,21},new[]{19,21})==19,"Deterministic heading under multi-select");
Check(ArsenalSpecPolicy.GroupFor(22,new[]{22},new[]{19})==22,"Native-hidden Test fixture stays outside selected groups");
using var doc=JsonDocument.Parse(File.ReadAllText(args[0]));
int units=0;
foreach(var row in doc.RootElement.EnumerateArray())
{
    int id=row.GetProperty("id").GetInt32();
    int[] memberships=row.GetProperty("specs").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
    Check(memberships.Length>0,"No membership: "+id);
    int primary=memberships[0];
    string snapshot=string.Join(",",memberships);
    for(int mask=0;mask<64;mask++)
    {
        int[] selected=Enumerable.Range(17,6).Where(s=>(mask&(1<<(s-17)))!=0).ToArray();
        int target=ArsenalSpecPolicy.GroupFor(primary,memberships,selected);
        Check(memberships.Contains(target),"Lost real membership: "+id);
        if(selected.Intersect(memberships).Any())
            Check(selected.Contains(target),"Visible unit under unselected heading: "+id);
        if(selected.Contains(primary)||selected.Length==0)
            Check(target==primary,"Original/All grouping changed: "+id);
        Check(string.Join(",",memberships)==snapshot,"Mutated game availability: "+id);
    }
    Check(ArsenalSpecPolicy.GroupFor(primary,memberships,Enumerable.Range(17,6).ToArray())==primary,"Reset restores primary heading: "+id);
    units++;
}
Console.WriteLine($"PASS: {checks} checks across {units} PLA units and all 64 specialization selections; shared-unit grouping and reset preserved");
