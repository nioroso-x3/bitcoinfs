#!/usr/bin/env python3
"""
Upload file to the Bitcoin network.
Requires configured bitcoin-cli access to a trusted local node with wallet access and some bitcoins to pay for the upload.
txfee is configured as 0.0005 BTC
Max file size is 16kb
Usage:
./tinyuploader.py filename >> bitcoinfs.conf
"""
from bitcoincmd import *
import os
if __name__ == "__main__":
   if len(sys.argv) != 2:
      print("Wrong number of arguments")
      exit()
   try:
       f = open(sys.argv[1],"rb").read()
       if len(f) > 16*1024:
           print("File too big! Use file2opreturn.py or another service.")
   except:
       print("Error opening file")
       exit()
   tx = btcGenOPRETURN(f)
   signed = btcSignTx(tx)
   txid = btcSendTx(signed)
   print(os.path.basename(sys.argv[1])+" "+txid)
