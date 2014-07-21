#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <member> <group> [<hightlighted>]"
    exit
fi

source ./creds.sh


highlighted=false
if [ "$3" != "" ] ; then
    highlighted=$3
fi


xml="<memberRef xmlns='urn:vpro:media:update:2009'  highlighted='$highlighted'>$2</memberRef>";

echo -e "Posting \n $xml"

echo curl -i -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data "$xml"  \
    ${target}
