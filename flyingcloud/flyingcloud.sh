#!/bin/bash

# TODO: install this with setuptools

function flyingcloud() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "You must run inside a Python virtual environment"
        exit 1
    fi

    # TODO: have main.py invoke sudo with correct environment variables
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

    if [ "$(uname)" == "Darwin" ]; then
        $VIRTUAL_ENV/bin/flyingcloud $@
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        sudo ${argv[@]} $VIRTUAL_ENV/bin/flyingcloud $@
    fi
}

flyingcloud $@
