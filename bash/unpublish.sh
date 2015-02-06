#!/bin/bash
source creds.sh

if [ -z "$1" ] ; then
    echo use "$0 <source mid>"
    exit
fi

source functions.sh


if [ -z "$2" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$2
fi


curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $(getUrl media/$1) | xsltproc  --stringparam publishStop $publishStop media_set_publishStop.xslt - > /tmp/media.xml

echo posting:
xmllint --format /tmp/media.xml

target=$(getUrl "media?errors=$errors")
echo result:
curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/media.xml  ${target}
echo
