#!/bin/bash
#set -x

if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <mid> <location id>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


target=$(getUrl media/$1/location/$2?errors=$errors)

curl -s --insecure --user $user -X DELETE ${target}
