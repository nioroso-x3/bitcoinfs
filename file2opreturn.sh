#!/bin/bash
#script to upload multiple chunks to the blockchain
#userpass is in the format user:password, corresponds to your bitcoind RPC user and password
#Example to upload file from the start
#./file2opreturn.sh user:pass dangerousfile.aes 1
#Output will be list of txids that make up the file.

userpass=$1
f=$2
startN=$3
out=$(./file2opreturn.py ${userpass} ${f} ${startN})
line=$(echo $out | grep 'Success\|Fail')
if echo $out | grep -q 'Success' ;
then
    v=(${line})
    endN=${v[2]}
    startN=$((startN + 1))
    echo $line
elif echo $out | grep -q 'Fail wait for new utxo' 
then
    echo "No available utxos"
    exit
else
    echo $line
    exit
fi

for i in $(seq $startN $endN)
do
    while :
    do
        out=$(./file2opreturn.py ${userpass} ${f} ${i})
        line=$(echo $out | grep 'Success\|Fail')
	if echo $out | grep -q 'Success' ; 
        then
            echo $line
            break
        elif echo $out | grep -q 'Fail wait for new utxo' 
        then
            #echo to stderr
            echo "Waiting for new utxo, sleeping 240 seconds" 1>&2
            sleep 240
        else
            echo "Other error ocurred"
            echo $line
            exit
        fi
    done
done

