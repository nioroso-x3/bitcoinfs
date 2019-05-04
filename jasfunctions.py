import subprocess
import json


def txid2boptreturn(txid):
    ''' return OP_RETURN in bytes given a txid'''
    literal1 = 'bitcoin-cli gettransaction ' + str(txid)
    bsv1 = subprocess.check_output(literal1,shell=True,stderr=subprocess.STDOUT,).decode("utf-8").strip('\x00')
    jbsv1 = json.loads(bsv1)
    literal2 = 'bitcoin-cli decoderawtransaction ' + jbsv1['hex']
    bsv2 = subprocess.check_output(literal2,shell=True,stderr=subprocess.STDOUT,).decode("utf-8").strip('\x00')
    jbsv2= json.loads(bsv2)
    opreturnhex=jbsv2['vout'][0]['scriptPubKey']['asm'].split('OP_RETURN')[1]
    return bytes.fromhex(opreturnhex)


#if __name__ == "__main__":
#    #'check'
#    a = txid2boptreturn('a87e72aaefaa38815d3e5bacb6643e18a7f1ae001aced8f5f0096e60a13d585f') 
#    print(a)
