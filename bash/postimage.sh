#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <mid> [<image.xml>]"
    exit
fi

if [ -z "$2" ] ; then
    imagexml="image.xml"
else
    imagexml=$2
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


target=$(getUrl media/$1/image?errors=$errors)

echo posting $imagexml

curl   -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data \@$imagexml \
    ${target}
error=$?
if [ $error != 0 ] ; then
    echo "Error: $error"
fi
