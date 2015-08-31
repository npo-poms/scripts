#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <form.xml>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh

writable=false

if [[ ! -z "$2" ]] ; then
    writable=$2
fi

curl -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @$1 \
    $(getUrl find)?writable=$writable
