#!/bin/bash

if [ -z "$1" ] ; then
    echo use "$0 <id>"
    exit
fi

source creds.sh
source functions.sh

target=$(getUrl program/$1/full)

echo $target >&2
curl -s --insecure --user $user --header "Content-Type: application/xml" -X GET \
    ${target} \
    | xmllint -format -
