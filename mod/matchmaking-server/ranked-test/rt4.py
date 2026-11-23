# Before 0.9.6 (3v3/5v5 team queue). The 0.9.6 2v2/3v3/4v4 queue is tested in rt14.py.
# Queue separation (Lateralus 22 Nov): 1v1 is its own solo queue; the team queue only makes 3v3 or 5v5.
import sys,os,time,json,urllib.request;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,stats
B='http://127.0.0.1:8652/hubs/test/hubs'
def fmt(xs):
    out={}
    for x in xs:
        g=x.got('MatchFound')
        out[x.name]=(g[-1][0]['format'],g[-1][0]['team']) if g else None
    return out
# 2 team solos + 2 1v1 solos: only the 1v1 pair matches; the team solos never get a 1v1
T=[C(B,f'a{i}',f'TeamSolo{i}') for i in range(2)];O=[C(B,f'b{i}',f'Duel{i}') for i in range(2)]
for x in T:x.call('FindMatch','rteam')
for x in O:x.call('FindMatch','r1v1')
time.sleep(2.5);print('2 team + 2 duel ->',fmt(T+O))
# 4 more team solos -> 3v3 with the 2 waiting
T2=[C(B,f'c{i}',f'TeamSolo{i+2}') for i in range(4)]
for x in T2:x.call('FindMatch','rteam')
time.sleep(2.5);print('6 team solos ->',fmt(T+T2))
# 10 team solos -> one 5v5, not 3v3 + 4 left
S=[C(B,f'd{i}',f'Ten{i}') for i in range(10)]
for x in S:x.call('FindMatch','rteam')
time.sleep(2.5);r=fmt(S);print('10 team solos ->',sorted(set(v[0] for v in r.values() if v)),sum(1 for v in r.values() if v),'matched')
# party of 2 in the 1v1 queue
P=[C(B,f'e{i}',f'Pair{i}') for i in range(2)]
P[0].call('PartyAction','invite',P[1].steam,None);time.sleep(0.2)
pid=P[1].call('PartyAction','state',None,None)['incoming'][0]['partyId'];P[1].call('PartyAction','accept',None,pid)
print('party of 2 r1v1 ->',P[0].call('FindMatch','r1v1'))
P[0].call('CancelFind')
# alias on the test hub: the unchanged client's 1v1 -> r1v1, 3v3 -> rteam
A=[C(B,f'7656119800000000{i}',f'Alias{i}') for i in range(2)]
for x in A:x.call('FindMatch','1v1')
time.sleep(2.5);m=A[0].got('MatchFound');print('alias 1v1 ->',m[-1][0]['mode'],m[-1][0]['format'],m[-1][0]['scenario'])
print('alias 3v3 queued as ->',(P[0].call('FindMatch','3v3'),P[0].call('GetRanked')['searching']))
P[0].call('CancelFind')
# rate the alias 1v1 and read the public profile
lid=m[-1][0]['lobbyId'];h=A[0] if m[-1][0]['host']==A[0].steam else A[1]
scen='[FA] [1v1] '+m[-1][0]['scenario']+' 0.2'
h.call('ReportGameLobby',lid,{'scenario':scen,'invite':{'x':1}});h.call('ReportStarted',lid)
side={0:'Alpha',1:'Bravo'}
print('GetRanked match',json.dumps(A[0].call('GetRanked')['match']))
for x in A:stats(B,x.steam,side[x.got('MatchFound')[-1][0]['team']],'Alpha')
time.sleep(0.5)
w=A[0] if A[0].got('MatchFound')[-1][0]['team']==0 else A[1]
p=json.load(urllib.request.urlopen(B+'/ranked/player/'+w.steam))
print('winner profile 1v1',json.dumps(p['me']['1v1']))
print('lookup of unknown id does not add a player:',json.load(urllib.request.urlopen(B+'/ranked/player/76561190000000000'))['me']['1v1']['place'],json.load(urllib.request.urlopen(B+'/ranked/leaderboard/1v1'))['players'])
