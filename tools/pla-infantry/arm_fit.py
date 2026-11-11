"""Fit arm centerlines without allowing a landmark cage to flatten cross-sections.

Upper/lower arms use proper rotations and length-only scaling. Hands use one
proper rotation, so palm/finger thickness is preserved before skinning.
"""
import numpy as np


def rotation_between(a,b):
 a=np.asarray(a,dtype=float);a=a/np.linalg.norm(a);b=np.asarray(b,dtype=float);b=b/np.linalg.norm(b)
 v=np.cross(a,b);c=float(np.dot(a,b))
 if c < -.999999:
  axis=np.cross(a,[1,0,0] if abs(a[0])<.8 else [0,1,0]);axis/=np.linalg.norm(axis)
  return 2*np.outer(axis,axis)-np.eye(3)
 vx=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
 return np.eye(3)+vx+vx@vx/(1+c)


def rigid_rotation(a,b):
 a=np.asarray(a);b=np.asarray(b);a=a/np.linalg.norm(a,axis=1)[:,None];b=b/np.linalg.norm(b,axis=1)[:,None]
 u,_,vt=np.linalg.svd(a.T@b);r=vt.T@u.T
 if np.linalg.det(r)<0:vt[-1]*=-1;r=vt.T@u.T
 return r


def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)


class ArmFit:
 def __init__(self,source,native,body_height):
  self.sides=[];self.audit=[]
  for suffix,side,sign in [('l','Left',1),('r','Right',-1)]:
   src=np.asarray([source[n+'_'+suffix] for n in ['upperarm','lowerarm','hand']],dtype=float)
   dst=np.asarray([native[side+n] for n in ['Arm','ForeArm','Hand']],dtype=float)
   dst[:,2]-=body_height*np.asarray([.75,.35,0])
   segments=[]
   for i in range(2):
    axis=src[i+1]-src[i];length=np.linalg.norm(axis);target=dst[i+1]-dst[i];scale=np.linalg.norm(target)/length;assert .5<scale<2
    segments.append((axis/length,length,rotation_between(axis,target),scale))
   a=[np.asarray(source[f+'_01_'+suffix])-src[2] for f in ['index','ring','thumb']]
   b=[np.asarray(native[side+'Hand'+f+'1'])-dst[2] for f in ['Index','Ring','Thumb']]
   hand=rigid_rotation(a,b);assert np.allclose(hand.T@hand,np.eye(3),atol=1e-8) and np.linalg.det(hand)>.999999
   self.sides.append((sign,src,dst,segments,hand))
   self.audit.append({'side':side,'method':'segment length fit; radial scale1; rigid palm/fingers','upper_length_scale':segments[0][3],'forearm_length_scale':segments[1][3],'hand_rotation_determinant':float(np.linalg.det(hand)),'body_height_compensated_m':body_height,'native_hand_offset_m':0})
 def deform(self,points):
  points=np.asarray(points,dtype=float);result=points.copy()
  for sign,src,dst,segments,hand in self.sides:
   choose=(sign*points[:,0]>.16)&(points[:,2]>.86);q=points[choose]
   if not len(q):continue
   mapped=[]
   for i,(axis,length,rotation,scale) in enumerate(segments):
    delta=q-src[i];along=delta@axis
    fitted=delta+along[:,None]*axis*(scale-1)
    mapped.append(dst[i]+fitted@rotation.T)
   hand_points=dst[2]+(q-src[2])@hand.T
   lower_axis=segments[1][0]
   elbow=smooth(((q-src[1])@lower_axis+.025)/.05)
   wrist=smooth(((q-src[2])@lower_axis+.012)/.024)
   arm=mapped[0]*(1-elbow[:,None])+mapped[1]*elbow[:,None]
   fitted=arm*(1-wrist[:,None])+hand_points*wrist[:,None]
   blend=smooth((sign*q[:,0]-.16)/.10)*smooth((q[:,2]-.86)/.10)
   result[choose]=q+(fitted-q)*blend[:,None]
  assert np.isfinite(result).all()
  return result
