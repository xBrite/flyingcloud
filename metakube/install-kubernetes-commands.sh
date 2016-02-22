#!/bin/bash -ex

# Install kube-aws and kubectly on Mac or Linux;
# installs to virtualenv if one is activated.

if [ "$(uname)" == "Darwin" ]; then
    PLATFORM="darwin"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    PLATFORM="linux"
fi

KUBECTL_VERSION="1.1.2"
KUBECTL_URL="https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/${PLATFORM}/amd64/kubectl"
KUBE_AWS_VERSION="0.3.0"
KUBE_AWS_URL="https://github.com/coreos/coreos-kubernetes/releases/download/v${KUBE_AWS_VERSION}/kube-aws-${PLATFORM}-amd64.tar.gz"

wget "$KUBECTL_URL"
wget "$KUBE_AWS_URL"
if [ -z "$VIRTUAL_ENV" ]; then
    mv kubectl /usr/local/bin
    tar -C /usr/local/bin -xzvf kube-aws-*.tar.gz
else
    chmod +x kubectl 
    mv kubectl $VIRTUAL_ENV/bin
    tar -C "$VIRTUAL_ENV/bin" -xzvf kube-aws-*.tar.gz
fi

rm kube-aws-*.tar.gz
