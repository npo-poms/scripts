#!/bin/bash

if [ -z "$1" ] ; then
    echo use "$0 <id>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


target=$(getUrl program/$1/full)

echo $target >&2
curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET \
    ${target} \
    | xmllint -format -
