#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <mid> [<location>]"
    exit
fi


source creds.sh

target=$rs/media/$1/location?errors=michiel.meeuwissen@gmail.com


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
