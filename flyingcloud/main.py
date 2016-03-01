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

    if os.geteuid() != 0 and platform.system() == "Linux":
        sudo_command = sh.Command('sudo')
        sudo_command([sys.executable] + sys.argv)
    else:
        AppLayer = DockerBuildLayer('flaskexample', 'app')
        AppLayer.CommandName = 'app'
        AppLayer.Description = 'appy stuff'
        AppLayer.USERNAME_VAR = 'EXAMPLE_DOCKER_REGISTRY_USERNAME'
        AppLayer.PASSWORD_VAR = 'EXAMPLE_DOCKER_REGISTRY_PASSWORD'

        DockerBuildLayer.main(
            defaults,
            AppLayer,
            description="Build a Docker images using SaltStack",
        )
