#!/bin/bash

function build-image() {
    IMAGE="$1"
    shift
    HERE="$(cd "$(dirname "$0")"; pwd)"

    if [ -z "$VIRTUAL_ENV" ]; then
        echo "You must run inside a Python virtual environment"
        exit 1
    fi

    # TODO: rename these
    declare -a envvars=( \
        EXAMPLE_DOCKER_REGISTRY_USERNAME \
        EXAMPLE_DOCKER_REGISTRY_PASSWORD \
        VIRTUAL_ENV \
        TMPDIR
    )
    argv=()

    for ev in ${envvars[@]}; do
        value="$(eval "echo \$$ev")"
        argv+=("$ev=$value")
    done

    sudo ${argv[@]} $VIRTUAL_ENV/bin/python $HERE/build-${IMAGE}.py $@
}

IMAGE="flask-example"
HERE="$(cd "$(dirname "$0")"; pwd)"
build-image $IMAGE $*
