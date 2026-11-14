import sys
sys.path.insert(0,'/home/sam/tars/work/ba-dev/replicas/codex/work/pla-0.8/purchased-20261113');from famread import read_fam
k=0
for bone,ss in read_fam(sys.argv[1]):
    for sb in ss:
        p=sb['pos'];b=[(round(min(p[i::3]),1),round(max(p[i::3]),1)) for i in range(3)]
        print(k,bone[:18],len(p)//3,(sb['tex'] or '')[-12:],'x',b[0],'y',b[1],'z',b[2]);k+=1
