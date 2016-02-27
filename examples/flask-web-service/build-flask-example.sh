#!/bin/bash

IMAGE="flask-example"
HERE="$(cd "$(dirname "$0")"; pwd)"
source "$HERE/build-image.sh"
build-image $IMAGE $*
