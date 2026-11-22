import sys,time,json;sys.path.insert(0,'/tmp/heli3')
from rt_client import C,stats
B='http://127.0.0.1:8652'
a=C(B,'100','Alice');b=C(B,'200','Bob')
print('find a',a.call('FindMatch','r1v1'));print('find b',b.call('FindMatch','r1v1'))
time.sleep(2.5)
ma=a.got('MatchFound');mb=b.got('MatchFound');print('MatchFound',ma,mb)
lid=ma[0][0]['lobbyId'];host=ma[0][0]['host']
h=a if host=='100' else b
print('report lobby',h.call('ReportGameLobby',lid,{'scenario':'[FA] [1v1] Kadaga 0.1','invite':{'x':1}}))
print('started',h.call('ReportStarted',lid))
ta=ma[0][0]['team'];tb=mb[0][0]['team']
side={0:'Alpha',1:'Bravo'}
print(stats(B,'100',side[ta],'Alpha'));print(stats(B,'200',side[tb],'Alpha'))
time.sleep(0.5)
print('result a',a.got('RankedResult'),'b',b.got('RankedResult'))
print('ranked a',json.dumps(a.call('GetRanked')))
print('board',json.dumps(a.call('GetRankedLeaderboard','1v1'))[:400])
