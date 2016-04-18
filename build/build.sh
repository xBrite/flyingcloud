#!/bin/bash
# -*- coding: utf-8 -*-

set -o
set -x

HERE="$(cd $(dirname "$0"); pwd)"
MAINROOT="$(cd "$(dirname "$0")/.."; pwd)"
VIRTUALENV_DIR="$MAINROOT/.env"
echo "working dir: $(pwd)"
echo "MAINROOT: $MAINROOT"

platform='unknown'
unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
   platform='linux'
elif [[ "$unamestr" == 'Darwin' ]]; then
   platform='darwin'
fi

if [ platform == 'linux' ]; then
    PACKAGES="$(cat $(dirname $0)/install_on_travis_ubuntu.txt)"
    if [ -n "$PACKAGES" ]; then
        echo "Calling apt-get install"
        sudo apt-get update
        sudo apt-get install --yes $PACKAGES
    fi
    curl -fsSL https://get.docker.com/ | sh
fi

docker run hello-world

date
id || whoami

if [ "$TRAVIS" == "true" ]
then
    echo "**> Travis detected."
fi

if [ -z "$VIRTUAL_ENV" ]; then
    echo "No virtualenv detected: this script must be run from an activated virtualenv."
    exit 1
else
    echo "Detected virtualenv $VIRTUAL_ENV"
fi

python "$MAINROOT/setup.py" develop

cd "$MAINROOT/examples/flask-web-app"
flyingcloud -h
flyingcloud --build sysbase
flyingcloud --build pybase
flyingcloud --build app
flyingcloud --build opencv
#flyingcloud --run testrunner

