#!/usr/bin/env python3


import subprocess as sb
import binascii
import sys
import json
def str2hex(data):
  if type(data) == str:
    return binascii.hexlify(data.encode('utf-8'))
  if type(data) == bytes:
    return binascii.hexlify(data)

def hex2data(data):
  return binascii.unhexlify(data).decode('utf-8')

btc2sat = 100000000

def call(cmd):
 return  sb.check_output(cmd,shell=False).decode("utf-8").strip()

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
  
def btcGenOPRETURN(data,txfee=0.0001):
  txid,vout = btcGetUnspent()
  change = str(float(btcGetBalance() - txfee*btc2sat)/btc2sat)
  addr = btcNewAddress() 
  inputs = "\"[{\\\"txid\\\":\\\"%s\\\",\\\"vout\\\":%s}]\"" % (txid,vout)
  outputs = "\"{\\\"data\\\":\\\"%s\\\",\\\"%s\\\":%s}\"" % (str(str2hex(data),"ascii"),addr,change)

  tx = sb.check_output("/usr/local/bin/bitcoin-cli createrawtransaction "+inputs+" "+outputs,shell=True,executable="/bin/bash" ).decode("utf-8").strip()
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
  
