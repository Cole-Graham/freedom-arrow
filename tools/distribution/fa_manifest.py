"""Publish the Freedom Arrow version list everywhere it is read, and sign it.

Lateralus 19 Nov 2026 (launcher self-update, "in a secure way", after the Notepad++ updater hijack): launchers from 1.1.9 read only
manifest/live.signed.json and refuse any list whose ECDSA P-256 signature does not match the public key compiled into them. The private
key is ~/.config/ba-codex/launcher-signing-key.pem on the BA deck and is never uploaded. The same bytes also go to manifest/live.json (launchers
1.1.5-1.1.8) and to the old Drive file (launchers up to 1.1.4), so every launcher sees one list.
"""
from pathlib import Path
import base64,datetime,json,subprocess,sys,tempfile,time,urllib.request
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec

ROOT=Path('/home/sam/tars/work/ba-dev/replicas/codex');sys.path.insert(0,str(ROOT/'bin'))
RCLONE='/nix/store/42rnb5c0v5pjzhlcx46ww02jpa917f23-rclone-1.74.4/bin/rclone';RCONF=str(Path.home()/'.config/ba-codex/r2-rclone.conf')
KEY=Path.home()/'.config/ba-codex/launcher-signing-key.pem'
CONTEXT=b'freedomarrow-manifest-v1\n'   # must equal SignedManifest.Context in the launcher
PUBLIC='MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEldksEagvrwoKFGwmy7XDip3JEB+AeHFQTn52LcUVl2BPxjwreE5BcR4DiIMlh0rfVicCMZXGfCBe+ZSKV5J5ew=='
LOCAL=ROOT/'work/build-install/live-manifest.json'
def rc(*args):return subprocess.run([RCLONE,'--config',RCONF,*args],check=True,capture_output=True,text=True).stdout
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ba-publish-manifest'}),timeout=60) as r:return r.read()

def envelope(data):
    key=serialization.load_pem_private_key(KEY.read_bytes(),None)
    pub=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
    assert pub==PUBLIC,'signing key does not match the launcher public key'
    sig=key.sign(CONTEXT+data,ec.ECDSA(hashes.SHA256()))
    return (json.dumps({'manifest':base64.b64encode(data).decode(),'signature':base64.b64encode(sig).decode()})+'\n').encode()

def opened(env):
    """The manifest bytes inside a signed envelope, checked against the public key like the launcher does."""
    d=json.loads(env);data=base64.b64decode(d['manifest'])
    pub=serialization.load_der_public_key(base64.b64decode(PUBLIC))
    pub.verify(base64.b64decode(d['signature']),CONTEXT+data,ec.ECDSA(hashes.SHA256()))
    return data

def publish(manifest,file_id):
    """Serial, then Drive (<=1.1.4), R2 live.json (1.1.5-1.1.8), R2 live.signed.json (1.1.9+); every copy read back."""
    from virgil_google import access_token
    old=json.loads(LOCAL.read_text()) if LOCAL.exists() else {}
    manifest['serial']=max(int(time.time()),int(old.get('serial',0))+1)
    for k in ('launcher','melonloader'):   # carried over unless the caller set them
        if k not in manifest and k in old:manifest[k]=old[k]
    data=(json.dumps(manifest,indent=2)+'\n').encode();env=envelope(data);assert opened(env)==data
    req=urllib.request.Request('https://www.googleapis.com/upload/drive/v3/files/'+file_id+'?uploadType=media',data=data,method='PATCH',headers={'Authorization':'Bearer '+access_token(),'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as response:response.read()
    assert json.loads(get('https://drive.google.com/uc?export=download&id='+file_id+'&revision='+stamp()))==manifest,'Drive manifest readback differs'
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp)/'live.json').write_bytes(data);(Path(tmp)/'live.signed.json').write_bytes(env)
        rc('copyto',str(Path(tmp)/'live.json'),'r2:freedomarrow/manifest/live.json','--header-upload','Cache-Control: no-cache')
        rc('copyto',str(Path(tmp)/'live.signed.json'),'r2:freedomarrow/manifest/live.signed.json','--header-upload','Cache-Control: no-cache')
    assert json.loads(get('https://freedomarrow.app/manifest/live.json?t='+stamp()))==manifest,'R2 manifest readback differs'
    assert opened(get('https://freedomarrow.app/manifest/live.signed.json?t='+stamp()))==data,'R2 signed manifest readback differs'
    LOCAL.with_suffix('.json.tmp').write_bytes(data);LOCAL.with_suffix('.json.tmp').replace(LOCAL)
    return manifest
