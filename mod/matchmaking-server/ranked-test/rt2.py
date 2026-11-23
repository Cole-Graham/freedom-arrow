import sys,time,json;import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,stats
B='http://127.0.0.1:8652/hubs/test/hubs'
def party(leader,members):
    for m in members:
        print(' invite',m.name,leader.call('PartyAction','invite',m.steam,None) and 'ok')
        time.sleep(0.2)
        inc=m.call('PartyAction','state',None,None)['incoming']
        pid=inc[0]['partyId'];m.call('PartyAction','accept',None,pid)
# 5-stack
P=[C(B,f'5{i}',f'Stack{i}') for i in range(5)];party(P[0],P[1:])
print('5-stack rteam ->',P[0].call('FindMatch','rteam'))
print('5-stack r1v1 ->',P[0].call('FindMatch','r1v1'))
print('5-stack rteam again ->',P[0].call('FindMatch','rteam'))
S=[C(B,f'6{i}',f'Solo{i}') for i in range(5)]
for s in S:s.call('FindMatch','rteam')
time.sleep(2.5)
mf=[x.got('MatchFound') for x in P+S]
teams={}
for x,g in zip(P+S,mf):
    if g:teams.setdefault(g[-1][0]['team'],[]).append(x.name)
print('5v5 teams',teams)
# 3v3: party of 2 + 4 solos
Q=[C(B,f'7{i}',f'Duo{i}') for i in range(2)];party(Q[0],Q[1:])
R=[C(B,f'8{i}',f'Three{i}') for i in range(4)]
print('duo rteam ->',Q[0].call('FindMatch','rteam'))
for r in R:r.call('FindMatch','rteam')
time.sleep(2.5)
teams={}
for x in Q+R:
    g=x.got('MatchFound')
    if g:teams.setdefault(g[-1][0]['team'],[]).append(x.name)
print('3v3 teams',teams)
# cancel
X=C(B,'91','Canceller');print('find',X.call('FindMatch','r1v1'),'ranked',X.call('GetRanked')['searching']);print('cancel',X.call('CancelFind'),X.call('GetRanked')['searching'])
# disputed 1v1
d1=C(B,'93','DisA');d2=C(B,'94','DisB');d1.call('FindMatch','r1v1');d2.call('FindMatch','r1v1');time.sleep(2.5)
m=d1.got('MatchFound')[-1][0];lid=m['lobbyId'];h=d1 if m['host']=='93' else d2
h.call('ReportGameLobby',lid,{'scenario':'[FA] [1v1] Dead Center 0.2','invite':{'x':1}});h.call('ReportStarted',lid)
side={0:'Alpha',1:'Bravo'};t1=m['team'];t2=d2.got('MatchFound')[-1][0]['team']
stats(B,'93',side[t1],'Alpha');stats(B,'94',side[t2],'Bravo');time.sleep(0.5)
print('disputed results',d1.got('RankedResult'),d2.got('RankedResult'))
# wrong map: unrated
e1=C(B,'95','MapA');e2=C(B,'96','MapB');e1.call('FindMatch','r1v1');e2.call('FindMatch','r1v1');time.sleep(2.5)
m=e1.got('MatchFound')[-1][0];lid=m['lobbyId'];h=e1 if m['host']=='95' else e2
h.call('ReportGameLobby',lid,{'scenario':'[FA] [5v5] Airport 0.2','invite':{'x':1}});h.call('ReportStarted',lid)
stats(B,'95','Alpha','Alpha');stats(B,'96','Bravo','Alpha');time.sleep(0.5)
print('wrong-map results',e1.got('RankedResult'))
# leave before start cancels
f1=C(B,'97','LeaveA');f2=C(B,'98','LeaveB');f1.call('FindMatch','r1v1');f2.call('FindMatch','r1v1');time.sleep(2.5)
lid=f1.got('MatchFound')[-1][0]['lobbyId'];print('leave',f2.call('LeaveLobby',lid));time.sleep(0.3);print('failed msgs',f1.got('MatchFailed'))
