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

TXFEE=0.0007 #necessary for 64kb op_returns

def GetChunk(user,fname,N):
    chunkS = 64*1024 #64 kbytes
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
    elif N >= chunkN:
        A=chunkN*chunkS
        data.seek(A,0)
        chunk = data.read(r)
    tx = btcGenOPRETURN_RPC(user,chunk,TXFEE) 
    if r > 0:
        chunkN += 1
    return tx,chunkN,r

if __name__ == "__main__":
    if len(sys.argv) == 4:
        n = int(sys.argv[3])-1
        assert(n>=0)
        try:
            tx,l,r = GetChunk(sys.argv[1],sys.argv[2],n)
        except noutxo:
            print("Fail wait for new utxo")
            exit(-1)
        except:
            print("Fail chunking")
            exit(-1)
        try:
            signed = btcSignRaw_RPC(sys.argv[1],tx)
        except:
            print("Fail signing")
            exit(-1)
        try:
            senttx = btcSendRaw_RPC(sys.argv[1],signed)
        except nofee:
            print("Fail sending, fee not enough")
            exit(-1)
        except:
            print("Fail sending")
            exit(-1)
        print("Success",n+1,l,sys.argv[2],senttx)
    else:
        print("Wrong number of arguments <user:pass> <file> <chunk N>\n",sys.argv)
