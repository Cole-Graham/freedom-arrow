"""lm_auto.py: ArmFit landmarks for bodies without a skeleton (25 Nov 2026, ROC infantry).
Input: body vertices in metres, feet at z=0, facing -Y, arms in A- or T-pose.
Shoulder from body proportions; fingertip = outermost vertices; elbow and wrist = centroids of
arm slices at Drillis-Contini fractions; finger bases from the rigged ROC Reservist hand, expressed
in a hand frame (long axis, forward = -Y). Only finger directions matter to ArmFit (rigid palm)."""
import numpy as np
# Reservist bones (metres): hand, index_01, ring_01, thumb_01 (left side)
RH=np.array([0.5622,-0.0251,1.1161]);RF={'index':np.array([0.6142,-0.0868,1.0454]),'ring':np.array([0.6292,-0.0461,1.0443]),'thumb':np.array([0.5541,-0.0581,1.0862])}
def frame(a):
    a=a/np.linalg.norm(a);f=np.array([0,-1.,0]);f=f-(f@a)*a;f/=np.linalg.norm(f);return a,f,np.cross(a,f)
_a,_f,_n=frame((RF['index']+RF['ring'])/2-RH)
TEMPLATE={k:np.array([(v-RH)@_a,(v-RH)@_f,(v-RH)@_n]) for k,v in RF.items()}
def slab(V,p,u,half=.015,rad=.07):
    d=V-p;along=d@u;perp=np.linalg.norm(d-np.outer(along,u),axis=1);m=(abs(along)<half)&(perp<rad)
    return V[m].mean(0) if m.sum()>=5 else p
def estimate(V,shoulder=(0.111,0.814),elbow=0.42,wrist=0.755,hands=None):
    """hands: vertices of a separate hand mesh (GTA bodies). Then the fingertip is its point farthest from the
    shoulder, the wrist its end nearest the shoulder, and the elbow is measured on the shoulder-wrist line."""
    V=np.asarray(V,float);H=V[:,2].max();out={}
    for s,sign in (('l',1),('r',-1)):
        side=V[sign*V[:,0]>0];xm=(sign*side[:,0]).max();T=side[sign*side[:,0]>xm-.02].mean(0)
        x0=sign*shoulder[0]*H;z0=shoulder[1]*H;near=V[(abs(V[:,0]-x0)<.02)&(abs(V[:,2]-z0)<.03)]
        S=np.array([x0,near[:,1].mean() if len(near) else 0.,z0])
        if hands is None:
            u=(T-S)/np.linalg.norm(T-S);L=np.linalg.norm(T-S)
            E=slab(V,S+elbow*L*u,u);W=slab(V,S+wrist*L*u,u)
        else:
            hv=np.asarray(hands,float);hv=hv[sign*hv[:,0]>0];r=np.linalg.norm(hv-S,axis=1)
            T=hv[r>r.max()-.02].mean(0);W=hv[r<r.min()+.03].mean(0)
            u=(W-S)/np.linalg.norm(W-S);E=slab(V,S+(elbow/wrist)*np.linalg.norm(W-S)*u,u,rad=.06)
        a,f,n=frame(T-W);scale=np.linalg.norm(T-W)/0.16
        if sign<0:   # mirror the template for the right hand: forward stays forward
            pass
        out['upperarm_'+s]=S;out['lowerarm_'+s]=E;out['hand_'+s]=W;out['tip_'+s]=T
        for k,(ca,cf,cn) in TEMPLATE.items():
            cn=cn if sign>0 else -cn   # n = a x f flips handedness with a mirrored a
            out[k+'_01_'+s]=W+scale*(ca*a+cf*f+cn*n)
    return {k:[float(x) for x in v] for k,v in out.items()}
