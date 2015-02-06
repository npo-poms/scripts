#!/bin/bash

if [ -z "$1" ] ; then
    echo use "$0 <id>"
    exit
fi



source creds.sh
source functions.sh

target=$(getUrl program/$(rawurlencode "$1"))

echo $target >&2

curl  -s --insecure -f  -o- --user $user --header "Content-Type: application/xml" -X GET \
    ${target} | xmllint -format -

status=${PIPESTATUS[0]}
if [ $status = 22 ] ; then
    echo "Error code > 400" >&2
fi
