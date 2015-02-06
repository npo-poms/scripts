#!/bin/bash

DIR=/tmp/unpublishlocations
mkdir -p $DIR
rm -rf $DIR/*
split -l 100 $1 $DIR/location.

if [ -z "$2" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$2
fi


for i in $DIR/* ; do
    echo $i
    while read line; do
        mid=${line%%,*}
        _locations=${line#*,}
        _locations=${_locations%\"}
        _locations=${_locations#\"}
        _locations=${_locations%\}}
        _locations=${_locations#\{}
        locations=(${_locations//,/ })
        for location in "${locations[@]}" ; do
            echo ${mid} ${location}
            ./unpublishLocation.sh ${mid} ${location} ${publishStop}
            sleep 1
        done
        echo
    done < $i
    rm  $i
    echo sleeping
    #sleep 120
done
