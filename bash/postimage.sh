#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <mid> [<image.xml>]"
    exit
fi
#set -x

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
source $(dirname ${SOURCE[0]})/creds.sh
source $(dirname ${SOURCE[0]})/functions.sh


if [ -z "$2" ] ; then
    imagexml="image.xml"
else
    if [ -e "$2" ] ; then
        imagexml=\@$2
    else
        read -r -d '' imagexml << EOF
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<image xmlns="urn:vpro:media:update:2009">
  <title>Image for $1</title>
  <imageLocation>
    <url>$2</url>
  </imageLocation>
</image>
EOF
    fi
fi



target=$(getUrl media/$1/image?errors=$errors)

echo posting "$imagexml"

$CURL   -s --insecure --user $user --header "Content-Type: application/xml" -X POST --data "$imagexml" \
    ${target}
error=$?
if [ $error != 0 ] ; then
    echo "Error: $error"
fi
