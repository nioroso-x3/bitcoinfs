#!/usr/bin/env python3
"""
Helper functions that interact with bitcoin-cli and bitcoind
"""

import subprocess as sb
import binascii
import sys
import json
import requests
import uuid

#paths to bitcoin-cli and bitcoin-tx
bitcoin_cli = "bitcoin-cli-sv"
bitcoin_tx = "bitcoin-tx-sv"

#btc to satoshis
btc2sat = 100000000

class Error(Exception):
   """Base class for other exceptions"""
   pass

class noutxo(Error):
   """Raised when getting a utxo fails"""
   pass

class nofee(Error):
    """Raised when fee is too low"""
    pass

txidAPI="https://api.blockchair.com/bitcoin-sv/raw/transaction/"

def gentmpfname():
    return "/tmp/"+str(uuid.uuid4())

def call(cmd):
    return  sb.check_output(cmd,shell=False).decode("utf-8").strip()

def txid2boptreturn(txid):
    try:
        ''' return OP_RETURN in bytes given a txid'''
        bsv1 = call([bitcoin_cli,"gettransaction",txid])
        jbsv1 = json.loads(bsv1)
        bsv2 = call([bitcoin_cli,"decoderawtransaction",jbsv1['hex']])
        jbsv2= json.loads(bsv2)
        opreturnhex=jbsv2['vout'][0]['scriptPubKey']['asm'].split(' ')[1]
        return bytes.fromhex(opreturnhex)
    except:
        #expects txid api
        print("No bitcoin-cli available, falling back to http api")
        raw = requests.get(txidAPI+txid)
        js = raw.json()
        opreturnhex = js['data'][txid]['decoded_raw_transaction']['vout'][0]['scriptPubKey']['asm'].split(' ')[1]
        return bytes.fromhex(opreturnhex)

def str2hex(data):
    if type(data) == str:
        return binascii.hexlify(data.encode('utf-8'))
    if type(data) == bytes:
        return binascii.hexlify(data)

def hex2data(data):
    return binascii.unhexlify(data).decode('utf-8')



def btcGetUnspent():
    utxo = sorted(json.loads(call([bitcoin_cli,"listunspent"])), key=lambda x: -int(x['vout']))
    if len(utxo) == 0:
        raise noutxo
    utxo_txid= utxo[0]["txid"]
    utxo_vout= utxo[0]["vout"]
    value = int(float(utxo[0]["amount"])*btc2sat)
    return utxo_txid,utxo_vout,value
def btcNewAddress():
    addr = call([bitcoin_cli,"getrawchangeaddress"])
    return addr
  
def btcGenOPRETURN(data,txfee=0.0005):
    txid,vout,value = btcGetUnspent()
    change = str(float(value - txfee*btc2sat)/btc2sat)
    addr = btcNewAddress() 
    tx = call([bitcoin_tx,"-create","in=%s:%s"%(txid,vout),
                                    "outdata=%s" % (str2hex(data).decode("utf-8")),
                                    "outaddr=%s:%s" %(change,addr)])
    return tx
#0.0007 for 64kb op_return
def btcGenOPRETURN_RPC(user,data,txfee=0.0005):
    '''RPC user:pass, data in hex'''
    fn = gentmpfname()
    txid,vout,value = btcGetUnspent()
    change = str(float(value - txfee*btc2sat)/btc2sat)
    addr = btcNewAddress()    
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "createrawtransaction", "params": [[{\"txid\":\"%s\",\"vout\":%s}], {\"data\":\"%s\",\"%s\":%s}]}' % (txid,vout,str2hex(data).decode("utf-8"),addr,change)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    out = json.loads(sb.check_output(" ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"]),shell=True).decode("utf-8"))
    if (out['error'] != None):
        raise Error
    return out['result']

def btcSignRaw_RPC(user,data):
    '''RPC user:pass, tx in hex'''
    fn = gentmpfname()
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "signrawtransaction", "params": ["%s"] }' % (data)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    out = json.loads(sb.check_output(" ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"]),shell=True).decode("utf-8"))
    if out['error'] != None:
        raise Error
    return out['result']['hex']

def btcSendRaw_RPC(user,data):
    '''RPC user:pass, signed tx in hex'''
    fn = gentmpfname()
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "sendrawtransaction", "params": ["%s"] }' % (data)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    cmd = " ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"])
    out = json.loads(sb.check_output(cmd,shell=True).decode("utf-8"))
    if out['error'] != None:
        if(out['error']['code'] == -26 and out['error']['message'] == "66: insufficient priority"):
            raise nofee
        raise Error
    return out['result']

def btcSignTx(tx):
    signed = call([bitcoin_cli, "signrawtransaction",tx])
    signed = json.loads(signed)['hex']
    return signed

def btcSendTx(signed):
    txid = call([bitcoin_cli,"sendrawtransaction",signed])
    return txid
  
if __name__ == "__main__":
    pass
    #test functions
#    txid,vout,value = btcGetUnspent()
#    addr = btcNewAddress()
#    print("TEST1",txid,vout,addr,value)
#    data = "aaaa"
#    tx = btcGenOPRETURN(data)
#    signed = btcSignTx(tx)
#    print("TX",tx)
#    print("S",signed)

#    data = "aaaa"
#    unsigned = btcGenOPRETURN_RPC(sys.argv[1],data)
#    print("RPC",unsigned)
