#!/bin/bash
DIR=/tmp/locations
mkdir -p /tmp/$DIR
rm -rf $DIR/*
split -l 100 $1 $DIR/location.

for i in $DIR/* ; do
    echo $i
    while read line; do
        arr=(${line//,/ })
        echo ${arr[0]} ${arr[1]}
        ./removelocation.sh ${arr[0]} ${arr[1]}
        echo
        sleep 1
    done < $i
    rm  $i
    echo sleeping
    sleep 120
done
