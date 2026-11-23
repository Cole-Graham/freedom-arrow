# Ranked lobby phases (Lateralus 22 Nov): no deck -> refused; join -> deck (60 s) -> reveal (5 s) -> launch; join timeout cancels.
import sys,os,time,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
n=C(B,'7656119900000201','NoDeck',deck=False);print('no deck ->',n.call('FindMatch','r1v1'))
a=C(B,'7656119900000202','A');b=C(B,'7656119900000203','B')
a.call('FindMatch','r1v1');b.call('FindMatch','r1v1');time.sleep(2.5)
m=a.got('MatchFound')[-1][0];lid=m['lobbyId'];h,o=(a,b) if m['host']==a.steam else (b,a)
print('after match:',h.call('GetRanked')['match']['phase'])
h.call('ReportGameLobby',lid,{'scenario':'[FA] [1v1] '+m['scenario']+' 0.2','invite':{'x':1}});time.sleep(1.5)
print('host lobby, guest not joined:',h.call('GetRanked')['match']['phase'])
o.call('ConfirmJoined',lid);time.sleep(1.5)
r=h.call('GetRanked')['match'];print('all joined:',r['phase'],r['phaseLeftMs'],'groupDecks',json.dumps(h.call('GetRanked')['groupDecks']))
