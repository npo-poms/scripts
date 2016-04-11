#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <source mid>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


if [ -z "$2" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$2
fi


$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $(getUrl media/$1) | xsltproc  --stringparam publishStop $publishStop media_set_publishStop.xslt - > /tmp/media.xml

echo posting:
xmllint --format /tmp/media.xml

target=$(getUrl "media?errors=$errors")
echo result:
$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/media.xml  ${target}
echo
