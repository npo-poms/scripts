#!/bin/bash
set -x
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <source mid> <location id>"
    exit
fi
SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


if [ -z "$3" ] ; then
    publishStop=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
else
    publishStop=$3
fi

xslt=$(dirname ${SOURCE[0]})/../xslt/location_set_publishStop.xslt
echo $xslt
echo $publishStop

curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $(getUrl media/$1/locations) | xsltproc  --stringparam id $2 --stringparam publishStop $publishStop  $xslt - > /tmp/location.xml

target=$(getUrl media/$1/location?errors=$errors)

curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/location.xml  ${target}
