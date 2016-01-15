#!/bin/bash

if [ -z "$1" ] ; then
    echo use "$0 <id> <offset> <max> <order>"
    exit
fi
SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh

offset=$2
max=$3
order=$4

target=$(getUrl group/$1/episodes?)
if [ ! -z "$offset" ] ; then
    target="$target&offset=$offset"
fi

if [ ! -z "$max" ] ; then
    target="$target&max=$max"
fi

if [ ! -z "$order" ] ; then
    target="$target&order=$order"
fi





echo $target >&2

$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X GET \
    "${target}" \
    | xmllint -format -
