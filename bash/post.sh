#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <update.xml>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


target=$(getUrl "media?errors=$errors&lookupcrid=true&validateInput=true")

echo $target >&2

$CURL -i -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$1 \
    ${target}
