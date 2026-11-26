"""drive_tree.py FOLDER_ID OUT.txt: recursive file list of a Drive folder (id|path|size), via virgil_google (read-only)."""
import sys,json
import argparse
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, '/home/sam/tars/work/ba-dev/replicas/codex/bin')
from virgil_google import GoogleError, access_token, api, q  # noqa: E402
from virgil_google import api, q
BASE='https://www.googleapis.com/drive/v3'
root,out=sys.argv[1],sys.argv[2];rows=[]
def walk(fid,path):
    tok=None
    while True:
        p={'q':f"'{fid}' in parents and trashed=false",'pageSize':1000,'fields':'nextPageToken,files(id,name,mimeType,size)','supportsAllDrives':'true','includeItemsFromAllDrives':'true'}
        if tok:p['pageToken']=tok
        r=api(f'{BASE}/files?'+q(p))
        for x in r.get('files',[]):
            if x['mimeType']=='application/vnd.google-apps.folder':walk(x['id'],path+x['name']+'/')
            else:rows.append((x['id'],path+x['name'],int(x.get('size',0))))
        tok=r.get('nextPageToken')
        if not tok:break
walk(root,'')
open(out,'w').write(''.join(f'{i}|{p}|{s}\n' for i,p,s in rows))
print(len(rows),'files',round(sum(s for *_,s in rows)/1e6,1),'MB')
