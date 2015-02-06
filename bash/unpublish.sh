#!/bin/bash
#set -x
if [ -z "$1" ] ; then
    echo use "$0 <source mid>"
    exit
fi


source creds.sh

if [ -z "$2" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$2
fi

curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $rs/media/$1 | xsltproc  --stringparam publishStop $publishStop media_set_publishStop.xslt - > /tmp/media.xml

echo posting:
xmllint --format /tmp/media.xml

target=$rs/media?errors=michiel.meeuwissen@gmail.com
echo result:
curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/media.xml  ${target}
echo
