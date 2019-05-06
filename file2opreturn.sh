#!/bin/bash
#script to upload multiple chunks to the blockchain
userpass=$1
f=$2
startN=$3
out=$(./file2opreturn.py ${userpass} ${f} ${startN})
if echo $out | grep -q 'Success' ;
then
    v=(${out})
    endN=${v[2]}
    startN=$((startN + 1))
    echo $out
elif echo $out | grep -q 'Fail wait for new utxo' 
then
    echo "No available utxos"
    exit
else
    echo "Other error occurred"
    exit
fi

for i in $(seq $startN $endN)
do
    while :
    do
        out=$(./file2opreturn.py ${userpass} ${f} ${i})
        if echo $out | grep -q 'Success' ; 
        then
            echo $out
            break
        elif echo $out | grep -q 'Fail wait for new utxo' 
        then
            #echo to stderr
            echo "Waiting for new utxo, sleeping 240 seconds" 1 >%2
            sleep 240
        else
            echo "Other error ocurred"
            echo $out
            exit
        fi
    done
done

