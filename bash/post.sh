#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <update.xml>"
    exit
fi


source ./creds.sh

target="$rs/media?errors=michiel.meeuwissen@gmail.com&lookupcrid=true"

echo $target >&2

curl -i -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$1 \
    ${target}
