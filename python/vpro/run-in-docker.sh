#!/usr/bin/env bash


docker run -v ~/conf:/root/conf -v $HOME/integrity-check-results:/root/integrity-check-results -v $(cd .. ; pwd):/build -w /build/vpro --entrypoint /usr/bin/make mihxil/npo-pyapi-make:latest ${1:-all}
