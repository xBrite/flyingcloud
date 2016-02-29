#!/usr/bin/env bash
set -e
#set -x

if [ "$(uname)" == "Darwin" ]; then
    PLATFORM="darwin"
    DOCKER="docker"
    INTERFACE="${INTERFACE:-en0}"
    HOST_IP_ADDR="$(ifconfig $INTERFACE | awk '/inet /{print $2}')"
    TARGET_IP_ADDR="$(docker-machine ip default)"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    PLATFORM="linux"
    DOCKER="sudo docker"
    INTERFACE="${INTERFACE:-eth0}"
    HOST_IP_ADDR="$(ifconfig $INTERFACE | awk '/inet addr/{split($2,a,":"); print a[2]}')"
    TARGET_IP_ADDR="127.0.0.1"
fi

APP="$1"
argv=()

if [ "$APP" == "example" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_flask_example:latest"
    HOST_PORT="${HOST_PORT:-80}"
    TARGET_PORT="${TARGET_PORT:-8080}"
    PUBLISH_PORT="${PUBLISH_PORT:-$HOST_PORT:$TARGET_PORT}"
    argv=(--publish="$PUBLISH_PORT")
    echo "Exposing $PUBLISH_PORT on $TARGET_IP_ADDR"
elif [ "$APP" == "opencv" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_opencv:latest"
elif [ "$APP" == "pybase" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_pybase:latest"
elif [ "$APP" == "sysbase" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_sysbase:latest"
fi

if [ -z "$IMAGE" ]; then
    echo 'You must provide an app parameter ("example", "opencv", "pybase", "sysbase") or set $IMAGE'
    exit 1
fi


$DOCKER run -d ${argv[@]} "$IMAGE"
