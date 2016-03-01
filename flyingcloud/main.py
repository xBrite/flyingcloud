#!/usr/bin/env python

from __future__ import unicode_literals, absolute_import, print_function

import os
import platform

import sh
import sys

from .base import DockerBuildLayer


def main():
    base_dir = os.path.abspath(os.getcwd())
    defaults = dict(
        base_dir=base_dir,
    )

    class NewLayer(DockerBuildLayer):
        pass

    # shared settings
    NewLayer.USERNAME_VAR = 'EXAMPLE_DOCKER_REGISTRY_USERNAME'
    NewLayer.PASSWORD_VAR = 'EXAMPLE_DOCKER_REGISTRY_PASSWORD'
    NewLayer.Registry = 'quay.io'
    NewLayer.RegistryDockerVersion = "1.17"
    NewLayer.Organization = 'cookbrite'
    NewLayer.AppName = 'flaskexample'
    NewLayer.LoginRequired = False
    NewLayer.SquashLayer = False
    NewLayer.PushLayer = False
    NewLayer.PullLayer = False

    if os.geteuid() != 0 and platform.system() == "Linux":
        sudo_command = sh.Command('sudo')
        sudo_command([sys.executable] + sys.argv)
    else:
        # TODO: get all these from yaml file
        app_layer = NewLayer('flaskexample', command_name='app')
        app_layer.CommandName = 'app'
        app_layer.Description = 'appy stuff'
        app_layer.ExposedPorts = [80]
        app_layer.SourceImageBaseName = 'flaskexample_opencv'
        app_layer.set_layer_defaults()

        app_layer.main(
            defaults,
            app_layer,
            description="Build Docker images using SaltStack",
        )
