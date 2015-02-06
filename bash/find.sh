#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <form.xml>"
    exit
fi

source ./creds.sh
source ./functions.sh

curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$1 \
    $(getUrl find)  | xmllint -format -
