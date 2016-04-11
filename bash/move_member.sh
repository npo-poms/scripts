#!/bin/bash

if [ -z "$1" ] ; then
    echo use "$0 <id> <from> <to>"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


target=$(getUrl group/$1/members?errors=$errors)

echo $target >&2
$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X PUT  ${target} -d"
<move xmlns='urn:vpro:media:update:2009'>
    <from>$2</from>
    <to>$3</to>
</move>"
