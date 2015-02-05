#!/bin/bash
#set -x
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <source mid> <target mid>"
    exit
fi


source creds.sh

tempdir=`mktemp -d copylocations.XXXX`

curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $rs/media/$1/locations | xsltproc  --stringparam tempDir $tempdir locations_split.xslt - > /dev/null

target=$rs/media/$2/location?errors=michiel.meeuwissen@gmail.com

for i in `ls $tempdir`; do
    cat $tempdir/$i | xmllint -format - | grep programUrl
    curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$tempdir/$i  ${target}
    echo
done

rm -rf $tempdir
