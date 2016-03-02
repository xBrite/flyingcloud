#!/bin/bash

# TODO: install this with setuptools

function flyingcloud() {
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

    sudo ${argv[@]} $VIRTUAL_ENV/bin/flyingcloud $@
}

flyingcloud $@
