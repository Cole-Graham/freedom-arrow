import importlib.util,json,hashlib,tempfile,unittest,zipfile
from pathlib import Path
s=importlib.util.spec_from_file_location('switch',Path(__file__).with_name('switch.py'));switch=importlib.util.module_from_spec(s);s.loader.exec_module(switch)
class Profiles(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.h=Path(self.tmp.name);self.g=self.h/'game';(self.h/'Downloads').mkdir();(self.g/'UserData/BAModManager').mkdir(parents=True);(self.g/'GameAssembly.dll').write_bytes(b'pinned-native');(self.g/'UserData/BAModManager/manifest.json').write_text(json.dumps({'packages':[{'name':'Freedom Arrow','info':{'id':'freedomarrow.gameplay','version':'old'},'files':[],'enabled':True}]}))
 def tearDown(self):self.tmp.cleanup()
 def package(self,kind,bad_offset=False):
  version='1' if kind=='pla' else 'test-live';label='PLA Build 1' if kind=='pla' else 'Live';base='UserData/FreedomArrow/';files={base+'compatibility.json':json.dumps({'game_assembly_sha256':switch.sha(self.g/'GameAssembly.dll')}).encode(),base+'test-core.bin':kind.encode()}
  if kind=='pla':
   inf={'weapons':{'QLU11':{'weaponId':11},'QTS11':{'weaponId':12},'QTS11_GL':{'weaponId':13}}};files[base+'pla-build.json']=json.dumps({'build':1,'infantry':inf}).encode();rules=[{'weaponId':11,'offset':[0,-.17,.22]},{'weaponId':12,'offset':[0,-.17,.196]},{'weaponId':13,'offset':[0,-.17,.196]}]
   if bad_offset:rules[0]['offset']=[0,0,0]
   files['UserData/FAModels/infantry-weapons.json']=json.dumps(rules).encode();files['UserData/FAModels/test-model.fam']=b'approved-model';files['Mods/FAModels.dll']=b'model-loader';files['Mods/FAMusic.dll']=b'music-loader';files['UserData/FAMusic/voice-presets.txt']=b'defaults'
  pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()};files[base+'payload-manifest.json']=json.dumps({'version':version,'sha256':{n:h for n,h in pins.items() if n.startswith(base)}}).encode()
  if kind=='pla':files[base+'pla-package-manifest.json']=json.dumps({'label':'PLA Build 1','build':1,'sha256':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()}}).encode()
  path=self.h/'Downloads'/('pla.bamod' if kind=='pla' else 'live.bamod')
  with zipfile.ZipFile(path,'w') as z:
   for n,v in files.items():z.writestr(n,v)
   z.writestr('mod.json',json.dumps({'id':'freedomarrow.gameplay','version':version,'name':label}))
  return {'kind':kind,'version':version,'label':label,'build':1,'file':path.name,'sha256':switch.sha(path)}
 def test_roundtrip_retains_assets_preferences_and_removes_old_gameplay(self):
  pla=self.package('pla');live=self.package('live');switch.install(pla,self.g,self.h);prefs=self.g/'UserData/FAMusic/voice-presets.txt';prefs.write_bytes(b'user-choice');r=switch.install(live,self.g,self.h);self.assertFalse((self.g/'UserData/FreedomArrow/pla-build.json').exists());self.assertEqual((self.g/'UserData/FAModels/test-model.fam').read_bytes(),b'approved-model');self.assertEqual(prefs.read_bytes(),b'user-choice');switch.install(pla,self.g,self.h);self.assertTrue((self.g/'UserData/FreedomArrow/pla-build.json').exists());self.assertEqual(prefs.read_bytes(),b'user-choice')
 def test_wrong_package_is_rejected_before_any_mutation(self):
  pla=self.package('pla');pla['sha256']='0'*64;old=(self.g/'UserData/BAModManager/manifest.json').read_bytes()
  with self.assertRaises(AssertionError):switch.install(pla,self.g,self.h)
  self.assertEqual(old,(self.g/'UserData/BAModManager/manifest.json').read_bytes())
 def test_lost_alignment_is_rejected_before_any_mutation(self):
  pla=self.package('pla',True)
  with self.assertRaises(AssertionError):switch.install(pla,self.g,self.h)
  self.assertFalse((self.g/'UserData/FAModels').exists())
 def test_preflight_never_installs(self):
  pla=self.package('pla');r=switch.install(pla,self.g,self.h,check=True);self.assertFalse(r['installed']);self.assertFalse((self.g/'UserData/FAModels').exists())
if __name__=='__main__':unittest.main()
