#!/usr/bin/env python3
"""
Helper functions that interact with bitcoin-cli
"""

import subprocess as sb
import binascii
import sys
import json
import requests
import uuid
txidAPI="https://api.blockchair.com/bitcoin-sv/raw/transaction/"

def gentmpfname():
    return "/tmp/"+str(uuid.uuid4())

def call(cmd):
    return  sb.check_output(cmd,shell=False).decode("utf-8").strip()

def txid2boptreturn(txid):
    try:
        ''' return OP_RETURN in bytes given a txid'''
        bsv1 = call(["bitcoin-cli","gettransaction",txid])
        jbsv1 = json.loads(bsv1)
        bsv2 = call(["bitcoin-cli","decoderawtransaction",jbsv1['hex']])
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

btc2sat = 100000000


def btcGetUnspent():
    utxo = json.loads(call(["bitcoin-cli","listunspent"]))
    try:
        utxo_txid= utxo[0]["txid"]
        utxo_vout= utxo[0]["vout"]
    except:
        print("No spendable utxos.")
    return utxo_txid,utxo_vout
def btcNewAddress():
    addr = call(["bitcoin-cli","getrawchangeaddress"])
    return addr
def btcGetBalance():
    #in satoshis
    balance = call(["bitcoin-cli","getbalance"])
    return int(float(balance)*btc2sat)
  
def btcGenOPRETURN(data,txfee=0.0005):
    txid,vout = btcGetUnspent()
    change = str(float(btcGetBalance() - txfee*btc2sat)/btc2sat)
    addr = btcNewAddress() 
    tx = call(["bitcoin-tx","-create","in=%s:%s"%(txid,vout),
                                    "outdata=%s" % (str2hex(data).decode("utf-8")),
                                    "outaddr=%s:%s" %(change,addr.split(":")[1])])
    return tx

#def btcGenOPRETURN_RPC(user,data,txfee=0.0005):
#    fn = gentmpfname()
#    txid,vout = btcGetUnspent()
#    change = str(float(btcGetBalance() - txfee*btc2sat)/btc2sat)
#    addr = btcNewAddress()    
#    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "createrawtransaction", "params": ["[{\"txid\":\"%s\",\"vout\":%s}]", "{\"data\":\"%s\"}", "{\"%s\":%s}"]}' % (txid,vout,str2hex(data).decode("utf-8"),addr,change)
#    tmpf = open(fn,"wb")
#    tmpf.write(js.encode("ascii"))
#    tmpf.close()
#    cnt = "'content-type: text/plain;'"
#    cmd = " ".join(["curl","-v","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"])
#    print(cmd)
#    out = json.loads(sb.check_output(" ".join(["curl","-v","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"]),shell=True).decode("utf-8"))
#    return out
#    return out['result']['hex']

def btcSignRaw_RPC(user,data):
    fn = gentmpfname()
    js = u'{"jsonrpc": "1.0", "id":"curltest", "method": "signrawtransaction", "params": ["%s"] }' % (data)
    tmpf = open(fn,"wb")
    tmpf.write(js.encode("ascii"))
    tmpf.close()
    cnt = "'content-type: text/plain;'"
    out = json.loads(sb.check_output(" ".join(["curl","-s","--user",user,"--data-binary",'"@%s"'%(fn),"-H",cnt,"http://127.0.0.1:8332/"]),shell=True).decode("utf-8"))
    return out['result']['hex']

def btcSendRaw_RPC(user,data):
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

def btcSignTx(tx):
    signed = call(["bitcoin-cli", "signrawtransaction",tx])
    signed = json.loads(signed)['hex']
    return signed

def btcSendTx(signed):
    txid = call(["bitcoin-cli","sendrawtransaction",signed])
    return txid
  
if __name__ == "__main__":
    #test functions
    #txid,vout = btcGetUnspent()
    #addr = btcNewAddress()
    #f = "deadbeef"
    #if len(sys.argv) > 1:
    #  f = open(sys.argv[1],"rb").read()
    #tx = btcGenOPRETURN(f)
    #signed = btcSignTx(tx)

    #print("TEST1",txid,vout,addr)
    #print("TX",tx)
    #print("S",signed)
    #data = "aaaa"
    #unsigned = btcGenOPRETURN_RPC(sys.argv[1],data)
    #print(unsigned)
