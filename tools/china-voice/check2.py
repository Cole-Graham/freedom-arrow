# Checker v2 (18 Nov 2026): the v1 check in gen_checked.py failed correct takes for three reasons that are not speech faults:
# STT writes model numbers as digits ("九九A" -> "99A", "歼二十S" -> "歼20S"), the Latin-word rule rejected designations that are in the script
# ("LY-1", "VT-5", "PHL-16"), and one fixed pinyin per character counted homophones/heteronyms as different (中弹/重弹 zhong-dan).
# Now: tokens are pinyin sets (all readings) for hanzi, single letters for Latin, and digit runs read both digit-by-digit and as a number;
# Latin words are only rejected when the script has none. Same tolerance as v1: same token count, at most max(1, n//5) tokens differ.
import re,itertools
from pypinyin import pinyin,Style
D='ling yi er san si wu liu qi ba jiu'.split()
def num(n):
    n=int(n)
    if n<10:return [D[n]]
    if n<100:return ([D[n//10]] if n>=20 else [])+['shi']+([D[n%10]] if n%10 else [])
    return None
def toks(s):
    parts=[[]]   # list of variant token lists
    for m in re.finditer(r'[一-鿿]|[A-Za-z]|[0-9]+',s or ''):
        g=m.group()
        if g.isdigit():
            vs=[[{D[int(c)]} | ({'yao'} if c=='1' else set()) for c in g]]
            c=num(g)
            if c and len(g)>1:vs.append([{x} for x in c])
        elif g.isascii():vs=[[{g.upper()}]]
        else:vs=[[set(pinyin(g,heteronym=True,style=Style.NORMAL)[0])]]
        parts=[p+v for p in parts for v in vs][:16]
    return parts
def check(zh,t):
    if not t or 'error' in t:return False,'no transcript'
    if t.get('events'):return False,'events '+','.join(t['events'])
    text=t.get('text','')
    if not re.search(r'[A-Za-z]',zh) and re.search(r'[A-Za-z]{2,}',text):return False,'latin words'
    if re.search(r'[a-z]{2,}',text):return False,'latin words'
    best=None
    for a,b in itertools.product(toks(zh),toks(text)):
        if len(a)!=len(b):continue
        d=sum(not (x&y) for x,y in zip(a,b))
        best=d if best is None else min(best,d)
    n=len(toks(zh)[0])
    if best is None:return False,f'{len(toks(text)[0])} tokens, script {n}'
    return best<=max(1,n//5),f'{best} differ'
