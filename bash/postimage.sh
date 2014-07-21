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


source ./creds.sh

target=$rs/media/$1/image?errors=michiel.meeuwissen@gmail.com

echo posting $imagexml

curl   -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data \@$imagexml \
    ${target}
error=$?
if [ $error != 0 ] ; then
    echo "Error: $error"
fi
