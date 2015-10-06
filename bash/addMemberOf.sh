#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <member> <group> [<hightlighted>]"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


highlighted=false
if [ "$3" != "" ] ; then
    highlighted=$3
fi


xml="<memberRef xmlns='urn:vpro:media:update:2009'  highlighted='$highlighted'>$2</memberRef>";

echo -e "Posting \n $xml"

target=$(getUrl media/$1/memberOf?errors=$errors)\&followMerges=true


curl -i -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data "$xml"  $target
