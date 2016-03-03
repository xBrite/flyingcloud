#!/usr/bin/env bash
set -e
set -x

if [ "$(uname)" == "Darwin" ]; then
    PLATFORM="darwin"
    DOCKER="docker"
    MACHINE_NAME="${MACHINE_NAME:-default}"
    INTERFACE="${INTERFACE:-en0}"
    HOST_IP_ADDR="$(ifconfig $INTERFACE | awk '/inet /{print $2}')"
    TARGET_IP_ADDR="$(docker-machine ip $MACHINE_NAME)"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    PLATFORM="linux"
    DOCKER="sudo docker"
    INTERFACE="${INTERFACE:-eth0}"
    HOST_IP_ADDR="$(ifconfig $INTERFACE | awk '/inet addr/{split($2,a,":"); print a[2]}')"
    TARGET_IP_ADDR="127.0.0.1"
fi

APP="$1"
argv=()

if [ "$APP" == "app" ]; then
    IMAGE="quay.io/cookbrite/flaskexample_app:latest"
    HOST_PORT="${HOST_PORT:-80}"
    TARGET_PORT="${TARGET_PORT:-8080}"
    LOCAL_PORT="$TARGET_PORT"
    PUBLISH_PORT="${PUBLISH_PORT:-$TARGET_PORT:$HOST_PORT}"
    argv=(--publish="$PUBLISH_PORT")
    if [ "$PLATFORM" == "darwin" ]; then
        PORT_FORWARDING="-f -N -L $LOCAL_PORT:localhost:$TARGET_PORT"
        if ! ps aux | grep "[s]sh.*$PORT_FORWARDING"; then
            docker-machine ssh $MACHINE_NAME $PORT_FORWARDING
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
