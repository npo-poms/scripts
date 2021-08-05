#!/bin/bash
if [ -z "$1" ] ; then
    echo use "$0 <path_to_config_file>"
    exit
fi

CONFIG_FILE="$1"

source $CONFIG_FILE

# Properties 'user', 'api_endpoint', 'input_dir' and 'env' should be included in the config file
if [ -z "$user" -o -z "$api_endpoint" -o -z "$input_dirs" -o -z "$env" ] ; then
    echo "Not all required config keys are present: 'user', 'api_endpoint', 'input_dirs' and 'env'"
    exit 1
fi

# Check whether directories exist
for input_dir in "${input_dirs[@]}"
do
    if [ ! -d "$input_dir" ] ; then
        echo "Directories $input_dir do not exist"
        exit 1
    fi
done

SOURCE=$(readlink  $BASH_SOURCE)
if [[ -z "$SOURCE" ]] ; then
    SOURCE=$BASH_SOURCE
fi
ERROR_LOG=$(dirname ${SOURCE[0]})/$env.error.log
LAST_ADDED_FILE=$(dirname ${SOURCE[0]})/$env.last_added_file.txt

touch $LAST_ADDED_FILE

last_filename=$(<$LAST_ADDED_FILE)
newer_command=""

if test -f "$last_filename"; then
    newer_command="-newer $last_filename "
    echo "file exists"
else
    newer_command="-mmin -5 "
    echo "No file was sent before yet. Copying only files that were modified in the last 5 minutes"
fi

# Find & sort XML-files from old to new in all provided directories
find ${input_dirs[*]} -type f -name "*.xml" $newer_command-printf "%T@ %p\n"| sort -n | while read timestamp newfile
do
    echo $newfile > $LAST_ADDED_FILE
    
    response=$(curl -X POST --data "@$newfile" --user "$user" --header "Content-Type: application/xml" --write-out "%{http_code}" --silent --output /dev/null $api_endpoint)
    if [ "$response" -ne "200" ]; then
        echo $(date)$'\t'$newfile$'\t'failed with status code $response >> $ERROR_LOG
    fi
    read -t 2
done
