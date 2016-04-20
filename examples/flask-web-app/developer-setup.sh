#!/usr/bin/env bash

HERE="$(cd $(dirname "$0"); pwd)"

declare -a envvars=( \
    VIRTUAL_ENV \
    TMPDIR
)
argv=()

for ev in ${envvars[@]}; do
    value="$(eval "echo \$$ev")"
    argv+=("$ev=$value")
done

SALT_CALL="sudo ${argv[@]} salt-call --local state.apply -l debug"

sudo rm -rf /srv/salt
sudo mkdir -p /srv
sudo ln -sf "$HERE/salt/opencv" /srv/salt
ls /srv/salt/
$SALT_CALL
echo
sudo rm -rf /srv/salt
sudo mkdir -p /srv
sudo ln -sf "$HERE/salt/app" /srv/salt
ls /srv/salt/
$SALT_CALL

