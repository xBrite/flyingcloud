#!/usr/bin/env bash
set -e
set -x

if [ "$(uname)" == "Darwin" ]; then
    PLATFORM="darwin"
    DOCKER="docker"
    DOCKER_MACHINE_NAME="${DOCKER_MACHINE_NAME:-default}"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    PLATFORM="linux"
    DOCKER="sudo docker"
fi

APP="$1"
argv=()

if [ "$APP" == "app" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_app:latest"
    CONTAINER_PORT="${CONTAINER_PORT:-80}"
    HOST_PORT="${HOST_PORT:-8080}"
    LOCAL_PORT="$HOST_PORT"
    PUBLISH_PORT="${PUBLISH_PORT:-$HOST_PORT:$CONTAINER_PORT}"
    argv=(--publish="$PUBLISH_PORT")
    if [ "$PLATFORM" == "darwin" ]; then
        PORT_FORWARDING="-f -N -L $LOCAL_PORT:localhost:$HOST_PORT"
        if ! ps aux | grep "[s]sh.*$PORT_FORWARDING"; then
            docker-machine ssh $DOCKER_MACHINE_NAME $PORT_FORWARDING
        fi
    fi
elif [ "$APP" == "opencv" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_opencv:latest"
elif [ "$APP" == "pybase" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_pybase:latest"
elif [ "$APP" == "sysbase" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_sysbase:latest"
fi

if [ -z "$IMAGE" ]; then
    echo 'You must provide an app parameter ("app", "opencv", "pybase", "sysbase") or set $IMAGE'
    exit 1
fi

$DOCKER run -d ${argv[@]} "$IMAGE"

# To kill image:
#   docker kill $(docker ps -q)
# To kill port forwarding:
#   ps aux| grep [s]sh.*:8080|awk '{print $2}'|xargs kill -9
