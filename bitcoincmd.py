#!/usr/bin/env python3


import subprocess as sb
import binascii
import sys
import json

def call(cmd):
 return  sb.check_output(cmd,shell=False).decode("utf-8").strip()

def txid2boptreturn(txid):
  ''' return OP_RETURN in bytes given a txid'''
  bsv1 = call(["bitcoin-cli","gettransaction",txid])
  jbsv1 = json.loads(bsv1)
  bsv2 = call(["bitcoin-cli","decoderawtransaction",jbsv1['hex']])
  jbsv2= json.loads(bsv2)
  opreturnhex=jbsv2['vout'][0]['scriptPubKey']['asm'].split('OP_RETURN')[1]
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

def btcSignTx(tx):
  signed = call(["bitcoin-cli", "signrawtransaction",tx])
  signed = json.loads(signed)['hex']
  return signed

def btcSendTx(signed):
  txid = call(["bitcoin-cli","sendrawtransaction",signed])
  return txid
  
if __name__ == "__main__":
  #test functions
  txid,vout = btcGetUnspent()
  addr = btcNewAddress()
  f = "deadbeef"
  if len(sys.argv) > 1:
    f = open(sys.argv[1],"rb").read()
  tx = btcGenOPRETURN(f)
  signed = btcSignTx(tx)

  print("TEST1",txid,vout,addr)
  print("TX",tx)
  print("S",signed)
  
