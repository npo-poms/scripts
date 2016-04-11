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

tag=$2


$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X GET  $(getUrl media/$1)?followMerges=false | xsltproc  --stringparam tag $tag media_add_tag.xslt - > /tmp/media.xml

echo posting:
xmllint --format /tmp/media.xml

target=$(getUrl "media?errors=$errors&followMerges=false")
echo $target result:
$CURL -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data @/tmp/media.xml  ${target}
echo
