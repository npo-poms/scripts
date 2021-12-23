#!/usr/bin/env bash
#set -x
#image=docker-proxy.vpro.nl/mihxil/npo-vpro-check:latest
export VPRO_CHECK_IMAGE=mihxil/npo-vpro-check:latest
export VPRO_CHECK_MOUNTS="-v $HOME/conf:/root/conf -v $HOME/.ssh:/root/.ssh -v $HOME/integrity-check-results:/root/integrity-check-results"

docker pull ${VPRO_CHECK_IMAGE}
docker run -it ${VPRO_CHECK_MOUNTS} ${VPRO_CHECK_IMAGE} ${1:-all} tunnel=true
#docker run -it ${mounts}  $image
