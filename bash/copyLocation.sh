#!/bin/bash
#set -x
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <source mid> <target mid>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh

tempdir=`mktemp -d copylocations.XXXX`

$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $(getUrl /media/$1/locations) | xsltproc  --stringparam tempDir $tempdir locations_split.xslt - > /dev/null

target=$(getUrl media/$2/location?errors=$errors)

for i in `ls $tempdir`; do
    cat $tempdir/$i | xmllint -format - | grep programUrl
    $CURL -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$tempdir/$i  ${target}
    echo
done

rm -rf $tempdir
