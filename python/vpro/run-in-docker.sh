#!/usr/bin/env bash


docker run -v ~/conf:/root/conf -v $(cd ..; pwd):/build -w /build/vpro --entrypoint /usr/bin/make mihxil/npo-pyapi-make:latest
