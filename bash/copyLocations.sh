#!/bin/bash

DIR=/tmp/copylocations
mkdir -p $DIR
rm -rf $DIR/*
split -l 100 $1 $DIR/copylocation.

for i in $DIR/* ; do
    echo $i
    while read line; do
        arr=(${line//,/ })
        echo ${arr[1]} ${arr[0]}
        ./copyLocation.sh ${arr[1]} ${arr[0]}
        echo
        sleep 4
    done < $i
    rm  $i
    echo sleeping
    sleep 120
done
