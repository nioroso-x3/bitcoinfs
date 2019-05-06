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
        signed = btcSignRaw_RPC(sys.argv[1],chunk)
        rdysend = btcSendRaw_RPC(sys.argv[1],signed)
        if r > 0:
            l+=1
        print(n+1,l,sys.argv[2],rdysend)
    else:
        print("Wrong number of arguments <user:pass> <file> <chunk N>\n",sys.argv)
