#!/usr/bin/env python

from __future__ import unicode_literals, absolute_import, print_function

import os
import platform

import sh
import sys

import yaml

from .base import DockerBuildLayer


def parse_project_yaml():
    class NewLayer(DockerBuildLayer):
        pass

    project_filename = os.path.join(os.getcwd(), "flyingcloud.yaml")
    with open(project_filename) as fp:
        project_info = yaml.load(fp)

    # shared settings
    # TODO: make these use defaults so they can be optional
    NewLayer.USERNAME_VAR = project_info['username_varname']
    NewLayer.PASSWORD_VAR = project_info['password_varname']
    NewLayer.Registry = project_info['registry']
    NewLayer.RegistryDockerVersion = project_info['registry_docker_version']
    NewLayer.Organization = project_info['organization']
    NewLayer.AppName = project_info['app_name']
    NewLayer.LoginRequired = project_info['login_required']
    NewLayer.SquashLayer = project_info['squash_layer']
    NewLayer.PushLayer = project_info['push_layer']
    NewLayer.PullLayer = project_info['pull_layer']

    return NewLayer

def main():
    base_dir = os.path.abspath(os.getcwd())
    defaults = dict(
        base_dir=base_dir,
    )

    NewLayer = parse_project_yaml()

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
