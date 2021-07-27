#!/bin/bash
if [ -z "$1" -o -z "$2" ] ; then
    echo use "$0 <path_to_input_dir> <path_to_config_file>"
    exit
fi

# set path to watch
DIR="$1"
# properties 'user' and 'api_endpoint'
CONFIG_FILE="$2"

source $CONFIG_FILE

# Key 'user' should be included in credentials file
if [ -z "$user" -o -z "$api_endpoint" ] ; then
    echo "Not all required config keys are present: 'user' and 'api_endpoint'"
    exit 1
fi

LAST_ADDED_FILE="last_added_file.txt"

touch $LAST_ADDED_FILE

last_filename=$(<$LAST_ADDED_FILE)
newer_command=""

if test -f "$last_filename"; then
    newer_command="-newer $last_filename "
    echo "file exists"
else
    newer_command="-mmin -60 "
    echo "no file exists. Copy only files that are modified in the last 60 minutes (the cron-job interval)"
fi

# Sort from old to new
find $DIR -type f -name "*.xml" $newer_command-printf "%T@ %p\n"| sort -n | while read timestamp newfile
do
    echo $newfile > $LAST_ADDED_FILE
    
    curl -X POST --data "@$newfile" --user "$user" --header "Content-Type: application/xml" $api_endpoint
done
