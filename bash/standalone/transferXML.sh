#!/bin/bash
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <path_to_input_dir> <path_to_config_file>"
    exit
fi

# set path to watch
DIR="$1"
# properties 'api_endpoint' and 'credentials'
CONFIG_FILE="$2"

source $CREDENTIALS

# Key 'user' should be included in credentials file
if [ -z "$user" -o -z "$api_endpoint" ] ; then
    echo "Not all required config keys are present: 'user' and 'api_endpoint'"
    exit 1
fi

find . -name *.xml

#inotifywait -m -r -e create -e moved_to $DIR |
#    while read dir action file; do
#        if [[ "$file" =~ .*xml$ ]]; then
#            echo "The file '$file' appeared in directory '$dir' via '$action'"
#            # do something with the file
#            curl -F "data=$file" --user $user --header "Content-Type: application/xml" $api_endpoint
#        fi
#    done