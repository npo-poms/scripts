#!/bin/bash
#set -x
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <source mid> <location id>"
    exit
fi


source creds.sh

if [ -z "$3" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$3
fi

curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $rs/media/$1/locations | xsltproc  --stringparam id $2 --stringparam publishStop $publishStop location_set_publishStop.xslt - > /tmp/location.xml

target=$rs/media/$1/location?errors=michiel.meeuwissen@gmail.com

cat /tmp/location.xml
curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/location.xml  ${target}
