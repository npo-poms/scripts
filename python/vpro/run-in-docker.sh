#!/usr/bin/env bash
#set -x
image=docker-proxy.vpro.nl/mihxil/npo-vpro-check:latest
mounts="-v $HOME/conf:/root/conf -v $HOME/.ssh:/root/.ssh -v $HOME/integrity-check-results:/root/integrity-check-results"

docker pull ${image}
docker run -it ${mounts} --entrypoint /usr/bin/make $image ${1:-all} jmx_binary=/root/jmxterm.jar tunnel=true
#docker run -it ${mounts}  $image
