#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os
from io import BytesIO

from flyingcloud import DockerBuildLayer


# TODO
# - fail if layer config dir is not present

class BuildFlaskExampleError(Exception):
    pass


class ExampleBuildLayer(DockerBuildLayer):
    USERNAME_VAR = 'EXAMPLE_DOCKER_REGISTRY_USERNAME'
    PASSWORD_VAR = 'EXAMPLE_DOCKER_REGISTRY_PASSWORD'
    Registry = 'quay.io'
    RegistryDockerVersion = "1.17"
    Organization = 'cookbrite'
    AppName = 'flaskexample'
    LoginRequired = False

    # TODO: reconsider these
    SquashLayer = False
    PushLayer = False
    PullLayer = False


class SystemBaseLayer(ExampleBuildLayer):
    CommandName = 'sysbase'
    Description = 'Build System Base Layer - Phusion'
    LayerSuffix = CommandName
    TargetImagePrefixName = "{}/{}/{}_{}".format(
            ExampleBuildLayer.Registry, ExampleBuildLayer.Organization, ExampleBuildLayer.AppName, CommandName)
    TargetImageName = TargetImagePrefixName + ":latest"
    SaltStateDir = LayerSuffix
    PullLayer = False

    def initialize_build(self, args, salt_dir):
        # TODO: move to flyingcloud base
        dockerfile_path = os.path.join(args.base_dir, salt_dir, "Dockerfile")
        assert os.path.exists(dockerfile_path)
        self.source_image_name = self.build_dockerfile(args, self.layer_timestamp_name, dockerfile=dockerfile_path)


class PythonBaseLayer(ExampleBuildLayer):
    CommandName = 'pybase'
    Description = 'Build Python Base Layer - modern Python 2.7.x'
    LayerSuffix = CommandName
    SourceImageName = SystemBaseLayer.TargetImageName
    TargetImagePrefixName = "{}/{}/{}_{}".format(
            ExampleBuildLayer.Registry, ExampleBuildLayer.Organization, ExampleBuildLayer.AppName, CommandName)
    TargetImageName = TargetImagePrefixName + ":latest"
    SaltStateDir = LayerSuffix


class OpenCvLayer(ExampleBuildLayer):
    CommandName = 'opencv'
    Description = 'Build OpenCV layer'
    LayerSuffix = CommandName
    SourceImageName = PythonBaseLayer.TargetImageName
    TargetImagePrefixName = "{}/{}/{}_{}".format(
            ExampleBuildLayer.Registry, ExampleBuildLayer.Organization, ExampleBuildLayer.AppName, CommandName)
    TargetImageName = TargetImagePrefixName + ":latest"
    SaltStateDir = CommandName


class FlaskExampleLayer(ExampleBuildLayer):
    CommandName = 'app'
    Description = 'Build Flask Example app'
    LayerSuffix = CommandName
    SaltStateDir = LayerSuffix
    SourceImageName = OpenCvLayer.TargetImageName
    TargetImagePrefixName = "{}/{}/{}_{}".format(
            ExampleBuildLayer.Registry, ExampleBuildLayer.Organization, ExampleBuildLayer.AppName, CommandName)
    TargetImageName = TargetImagePrefixName + ":latest"
    Dockerfile = """
            FROM {}
            EXPOSE 80
    """.format(SourceImageName)

    def initialize_build(self, namespace, salt_dir):
        # expose ports via Dockerfile
        # TODO: autoexpose
        fileobj = BytesIO(self.Dockerfile.encode('utf-8'))
        self.build_dockerfile(namespace, self.layer_timestamp_name, fileobj=fileobj)


class FlaskExampleTestLayer(ExampleBuildLayer):
    CommandName = 'tests'
    Description = 'Build Flask Tests Layer'
    LayerSuffix = CommandName
    SourceImageName = FlaskExampleLayer.TargetImageName
    TargetImagePrefixName = "{}/{}/{}_{}".format(
            ExampleBuildLayer.Registry, ExampleBuildLayer.Organization, ExampleBuildLayer.AppName, CommandName)
    TargetImageName = TargetImagePrefixName + ":latest"
    SaltStateDir = CommandName


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    defaults = dict(
            base_dir=base_dir,
    )

    # TODO: discovery mechanism
    ExampleBuildLayer.main(
            defaults,
            SystemBaseLayer,
            PythonBaseLayer,
            OpenCvLayer,
            FlaskExampleLayer,
            description="Build a Flask example Docker image using SaltStack",
    )


if __name__ == '__main__':
    main()
