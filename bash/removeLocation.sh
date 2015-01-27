#!/bin/bash
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <mid> <location id>"
    exit
fi


source creds.sh

target=$rs/media/$1/location/$2?errors=michiel.meeuwissen@gmail.com

curl -i -s --insecure --user $user --header "Content-Type: application/xml" -X DELETE --data "$xml"  \
    ${target}
