using FreedomArrow;
using System.Text.Json.Nodes;
using System.Security.Cryptography;
int checks=0;
void Check(bool value){if(!value)throw new Exception("Identity test failed");checks++;}
Check(BuildIdentity.ResolveLabel("4","4",4,"PLA TEST Build 4")=="PLA TEST Build 4");
foreach(var values in new[]{new[]{"1","4","4","PLA TEST Build 4"},new[]{"4","3","4","PLA TEST Build 4"},new[]{"4","4","3","PLA TEST Build 4"},new[]{"4","4","4","Freedom Arrow 1"},new[]{"0","0","0","PLA TEST Build 0"}}){bool refused=false;try{BuildIdentity.ResolveLabel(values[0],values[1],int.Parse(values[2]),values[3]);}catch(InvalidDataException){refused=true;}Check(refused);}
string root=Path.Combine(Path.GetTempPath(),"pla-identity-"+Guid.NewGuid());Directory.CreateDirectory(Path.Combine(root,"UserData"));
try{string f=Path.Combine(root,"UserData","helmet.fas");File.WriteAllText(f,"new helmet");var hashes=new JsonObject{["UserData/helmet.fas"]=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(f))).ToLowerInvariant()};Check(PayloadVerifier.Verify(root,hashes)==1);File.WriteAllText(f,"old helmet");bool refused=false;try{PayloadVerifier.Verify(root,hashes);}catch(InvalidDataException){refused=true;}Check(refused);}finally{Directory.Delete(root,true);}
Console.WriteLine($"PASS: {checks} checks; mixed build metadata and stale helmet files refused");
