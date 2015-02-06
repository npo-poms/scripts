
environments=("prod=https://api.poms.omroep.nl/media" "test=https://api-test.poms.omroep.nl/media" "dev=https://api-dev.poms.omroep.nl/media" "localhost=http://localhost:8071/rs/media")

if [ "$DEBUG" = 'true' ]  ; then
    # Use DEBUG=true as prefix to toggle this
    set -x
fi

trap "exit 1" TERM
export TOP_PID=$$

getUrl() {
    path=$1
    if [ ! -z "$ENV" ] ; then
        for env  in "${environments[@]}" ; do
            if [ ${env%%=*} == $ENV ] ; then
                echo "${env##*=}/$path"
                return
            fi
        done
        echo "Not recognized $ENV. Use one of ${environments[@]}" 1>&2
        kill -s TERM $TOP_PID
    fi
    if [ -z "$rs"] ; then
        ENV=prod getUrl $path
    else
        echo $rs/$path
    fi
    return
}


rawurlencode() {
    local string="${1}"
    local strlen=${#string}
    local encoded=""

    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-_.~a-zA-Z0-9] ) o="${c}" ;;
            * )               printf -v o '%%%02x' "'$c"
        esac
        encoded+="${o}"
    done
    echo "${encoded}"    # You can either set a return variable (FASTER)
    REPLY="${encoded}"   #+or echo the result (EASIER)... or both... :p
}
