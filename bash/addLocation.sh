#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <mid> [<location>]"
    exit
fi

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh

target=$(getUrl rs/media/$1/location?errors=$errors)


if [ -e $2 ] ; then
    xml=@$2
else
    xml="<location xmlns='urn:vpro:media:update:2009'>
 <programUrl>$2</programUrl>
</location>"
fi



echo -e "Posting \n $xml"

curl -i -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data "$xml"  \
    ${target}
