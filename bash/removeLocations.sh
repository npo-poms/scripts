#!/bin/bash
while read line; do
    arr=(${line//,/ })
    ./removelocation.sh ${arr[0]} ${arr[1]}
done < $1
