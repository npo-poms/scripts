#!/bin/bash
set -x
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

curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $rs/media/$1/locations | xsltproc  --stringparam id $2 --stringparam publishStop $publishStop location_set_publishStop.xslt -

exit
target=$rs/media/$2/location?errors=michiel.meeuwissen@gmail.com

for i in `ls $tempdir`; do
    cat $tempdir/$i | xmllint -format - | grep programUrl
    curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$tempdir/$i  ${target}
    echo
done

rm -rf $tempdir
