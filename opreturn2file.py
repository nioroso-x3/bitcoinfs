#!/usr/bin/env python3
"""
Generates curl commands to send files by chunks
For now you have to rerun this script each time you upload a chunk and run the command for the chunk you want to upload.
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

def chunker(fname):
    chunks = []
    chunkS = 48*1024
    data = open(fname,"rb").read()
    l = len(data)
    chunkN = int(l / chunkS)
    r = l - chunkN*chunkS
    for i in range(chunkN):
        begin = i*chunkS
        end = i+1*chunkS
        chunk = data[begin:end]
        tx = btcGenOPRETURN(chunk)
        chunks.append(tx)
    begin=chunkN*chunkS
    end=begin+r
    chunk = data[begin:end]
    chunktx = btcGenOPRETURN(bytes(chunk))
    tx = btcGenOPRETURN(chunk)
    chunks.append(tx)
    return chunks


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
    chunks = chunker(sys.argv[2])
    cmds = []
    for chunk in chunks:
        signed = signrawRPC(sys.argv[1],chunk)
        rdysend = sendrawRPC(sys.argv[1],signed)
        cmds.append(rdysend)
    for cmd in cmds:
        print(cmd)
