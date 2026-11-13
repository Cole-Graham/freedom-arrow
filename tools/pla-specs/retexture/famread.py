import struct
def read_fam(path):
    d=open(path,'rb').read();o=0
    def i32():
        nonlocal o;v=struct.unpack_from('<i',d,o)[0];o+=4;return v
    def f32(n):
        nonlocal o;v=struct.unpack_from('<%df'%n,d,o);o+=4*n;return v
    def s():
        nonlocal o;n=i32();v=d[o:o+n].decode();o+=n;return v
    assert d[:4]==b'FAM1';o=4;parts=[]
    for _ in range(i32()):
        bone=s();subs=[]
        for _ in range(i32()):
            tex=s();col=f32(4);nv=i32();pos=f32(3*nv);nrm=f32(3*nv);uv=f32(2*nv);ni=i32();idx=struct.unpack_from('<%di'%ni,d,o);o+=4*ni
            subs.append(dict(tex=tex,col=col,pos=pos,nrm=nrm,uv=uv,idx=idx))
        parts.append((bone,subs))
    assert o==len(d);return parts
