"""Keep #build-install as fixed posts: the install guide, the current build, then the music pack (edited in place).
Usage: update.py VERSION BAMOD_PATH DOWNLOAD_LINK. Instruction wording is frozen; change only links and versions.
The .bamod is over Discord's upload limit, so the post links to a public Drive copy; upload it first and check its hash."""
import sys,json,hashlib,uuid,datetime
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex')
from virgil import discord_client as dc
H=Path(__file__).parent;S=json.loads((H/'state.json').read_text());ch=S['channel']
def patch(mid,content,file=None):
    assert len(content)<2000,len(content)
    # Osama, 10 Nov: public install posts have no edit logs; PLA TEST is internal.
    assert 'Document change log' not in content, 'Keep edit history out of #build-install'
    assert 'PLA TEST' not in content, 'PLA TEST is internal; do not publish it here' 
    p={'content':content,'allowed_mentions':{'parse':[]}}
    if not file:
        p['attachments']=[]
        return dc._send('PATCH',f'/channels/{ch}/messages/{mid}',json.dumps(p).encode(),'application/json')
    b='----FA'+uuid.uuid4().hex;f=Path(file);p['attachments']=[{'id':0,'filename':f.name}]
    body=(f'--{b}\r\nContent-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n{json.dumps(p)}\r\n'
          f'--{b}\r\nContent-Disposition: form-data; name="files[0]"; filename="{f.name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+f.read_bytes()+f'\r\n--{b}--\r\n'.encode()
    return dc._send('PATCH',f'/channels/{ch}/messages/{mid}',body,f'multipart/form-data; boundary={b}',300)
# Frozen by Osama: edit instruction wording only on an explicit human request.
if S.get('instructions_locked'):
    for key, expected in S['instruction_template_sha256'].items():
        assert hashlib.sha256((H/(key+'.md')).read_bytes()).hexdigest()==expected, 'Instruction text changed: '+key
V,F,L=sys.argv[1],sys.argv[2],sys.argv[3]
# Multiplayer lock (Osama, 7 November 2026): while state.json has "locked", the build post stays on that version so every
# player keeps the same build code. Only Osama or Lateralus lifts it: remove "locked" from state.json.
if S.get('locked') and S['locked']!=V:sys.exit(f"#build-install is locked to {S['locked']} for multiplayer; not posting {V}. Remove 'locked' from state.json only when Osama or Lateralus says so.")
sha=hashlib.sha256(Path(F).read_bytes()).hexdigest()
# The approved first-time setup post is not republished during routine version updates.
now=datetime.datetime.now(ZoneInfo('America/Los_Angeles'));D=now.strftime('%-d %B %Y');STAMP=now.strftime('%Y-%m-%d %H:%M:%S %Z')
# Lateralus, 10 Nov: a published build must update the stable manifest too.
import subprocess
publisher=Path('/home/sam/tars/work/ba-dev/replicas/codex/bin/ba-publish-manifest')
if S.get('manifest_file_id'):
    subprocess.run([str(publisher),V,F,L],check=True)
for key in ['build']:
    content=(H/(key+'.md')).read_text().replace('{V}',V).replace('{LINK}',L)
    current=dc.get(f'/channels/{ch}/messages/{S[key]}')
    if current['content'].strip()!=content.strip():patch(S[key],content)
for key in ['music']:
    content=(H/(key+'.md')).read_text().replace('{ASSET_VERSION}',S['assets_version']).replace('{ASSET_LINK}','<'+S['assets_link']+'>')
    current=dc.get(f'/channels/{ch}/messages/{S[key]}')
    if current['content'].strip()!=content.strip():patch(S[key],content)
S.update(current_gameplay=V,gameplay_link=L)
(H/'state.json').write_text(json.dumps(S,indent=2)+'\n')
# Retention runs through the same guarded helper and daily timer; it never bypasses GitHub caps.
subprocess.run(['systemctl','--user','start','--no-block','ba-hosted-retention.service'],check=True)

print('Windows and Linux download posts updated; instruction wording preserved.')
for x in reversed(dc.get(f'/channels/{ch}/messages?limit=10')):print(x['id'],x['author']['username'],[a['filename'] for a in x.get('attachments',[])],x['content'][:60].replace('\n',' | '))
