#!/usr/bin/env python3
"""
Generates curl commands to send files by 48kb chunks
Needs user:pass, file and chunk number as argument:
"""
import subprocess as sb
import binascii
import sys
import json
from bitcoincmd import *
import sys
import uuid
def gentmpfname():
  return "/tmp/"+str(uuid.uuid4())

def GetChunks(fname):
    chunks = []
    chunkS = 48*1024
    data = open(fname,"rb")
    data.seek(0,2)
    l = data.tell()
    data.seek(0,0)
    chunkN = int(l / chunkS)
    r = l - chunkN*chunkS
    for i in range(chunkN):
        chunk = data.read(chunkS)
        tx = btcGenOPRETURN(chunk)
        chunks.append(tx)
    chunk = data.read(r)
    tx = btcGenOPRETURN(chunk)
    chunks.append(tx)
    return chunks

def GetChunk(fname,N):
    chunkS = 48*1024
    data = open(fname,"rb")
    data.seek(0,2)
    l = data.tell()
    data.seek(0,0)
    chunkN = int(l / chunkS)
    r = l - chunkN*chunkS
#    print(N,chunkN,l,chunkS,r)
    if N < chunkN:
        A = N*chunkS
        data.seek(A,0)
        chunk = data.read(chunkS)
        tx = btcGenOPRETURN(chunk) 
        return tx,chunkN,r
    elif N >= chunkN:
        A=chunkN*chunkS
        data.seek(A,0)
        chunk = data.read(r)
        tx = btcGenOPRETURN(chunk)
        return tx,chunkN,r

def signrawRPC(user,data):
    fn = gentmpfname()
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "signrawtransaction", "params": ["%s"] }' % (data)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    out = json.loads(sb.check_output(" ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"]),shell=True).decode("utf-8"))
    return out['result']['hex']

def sendrawRPC(user,data):
    fn = gentmpfname()
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "sendrawtransaction", "params": ["%s"] }' % (data)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    cmd = " ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"])
    return cmd
    #out = json.loads(sb.check_output(cmd,shell=True).decode("utf-8"))
    #return out['result']['hex']


if __name__ == "__main__":
#    if len(sys.argv) == 3:
#        chunks = GetChunks(sys.argv[2])
#        cmds = []
#        for chunk in chunks:
#            signed = signrawRPC(sys.argv[1],chunk)
#            rdysend = sendrawRPC(sys.argv[1],signed)
#            cmds.append(rdysend)
#        for cmd in cmds:
#            print(cmd)
    if len(sys.argv) == 4:
        n = int(sys.argv[3])-1
        assert(n>=0)
        chunk,l,r = GetChunk(sys.argv[2],n)
        signed = signrawRPC(sys.argv[1],chunk)
        rdysend = sendrawRPC(sys.argv[1],signed)
        if r > 0:
            l+=1
        print(n+1,l,rdysend)
    else:
        print("Wrong number of arguments\n",sys.argv)
