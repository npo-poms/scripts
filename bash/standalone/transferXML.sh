#!/bin/bash
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <path_to_input_dir> <path_to_config_file>"
    exit
fi

# set path to watch
DIR="$1"
# properties 'api_endpoint' and 'credentials'
CONFIG_FILE="$2"

source $CONFIG_FILE

# Key 'user' should be included in credentials file
if [ -z "$user" -o -z "$api_endpoint" ] ; then
    echo "Not all required config keys are present: 'user' and 'api_endpoint'"
    exit 1
fi

PREV_RESULT_FILE="prev_result.txt"
NEW_RESULT_FILE="new_result.txt"

find $DIR -type f -name "*.xml" -print > $NEW_RESULT_FILE

if test -f "$PREV_RESULT_FILE"; then
    echo "$PREV_RESULT_FILE exists."
    # Only show newlines in $NEW_RESULT_FILE
    comm -13 $PREV_RESULT_FILE $NEW_RESULT_FILE | while read newfile
    do
        echo $newfile
        # TODO: finish API-call
        curl -F "data=$newfile" --user $user --header "Content-Type: application/xml" $api_endpoint
    done
else
    echo "previous result doesn't exist yet"
fi

mv $NEW_RESULT_FILE $PREV_RESULT_FILE


#inotifywait -m -r -e create -e moved_to $DIR |
#    while read dir action file; do
#        if [[ "$file" =~ .*xml$ ]]; then
#            echo "The file '$file' appeared in directory '$dir' via '$action'"
#            # do something with the file
#            curl -F "data=$file" --user $user --header "Content-Type: application/xml" $api_endpoint
#        fi
#    done