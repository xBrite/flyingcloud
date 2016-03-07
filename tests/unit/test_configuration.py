# -*- coding: utf-8 -*-
import os

import pytest

from flyingcloud import DockerBuildLayer, FlyingCloudError
from flyingcloud.main import get_project_info, parse_project_yaml


class TestConfiguration:
    def test_parse_yaml(self, tmpdir):
        salt_dir = tmpdir.mkdir("salt")
        project_file = tmpdir.join("flyingcloud.yaml")
        project_file_content = """
layers:
  - app
username_varname: EXAMPLE_DOCKER_REGISTRY_USERNAME
password_varname: EXAMPLE_DOCKER_REGISTRY_PASSWORD
registry: quay.io
organization: cookbrite
registry_docker_version: "1.17"
app_name: 'flaskexample'
login_required: false
squash_layer: false
push_layer: false
pull_layer: false
        """
        project_file.write(project_file_content)
        app_dir = salt_dir.mkdir("app")
        layer_file = app_dir.join("layer.yaml")
        layer_file_content = """
description: Build Flask Example app
parent: opencv
exposed_ports:
  - 80
        """
        layer_file.write(layer_file_content)
        expected_project_name = os.path.basename(str(tmpdir.realpath()))
        project_name, project_info, layers_info = get_project_info(str(tmpdir.realpath()))
        assert project_name is not None
        assert project_info is not None
        assert layers_info is not None
        assert expected_project_name == project_name
        assert len(layers_info) == 1
        assert len(project_info['layers']) == 1

    def test_parse_project_yaml(self):
        project_name = "flaskexample"
        project_info = {
            'layers': ['app'],
            'app_name': 'flaskexample',
            'registry' : {
                'host': 'quay.io',
                'organization': 'cookbrite',
                'registry_docker_version': "1.17",
                'login_required': False,
                'squash_layer': False,
                'push_layer': False,
                'pull_layer': False
            }
        }
        layers_info = {'app':
           {
               'info': {
                   'help': 'Build Flask Example app',
                   'parent': 'opencv',
                   'exposed_ports': [80]
               },
               'path': '/'
           }
        }
        layers = parse_project_yaml(project_name=project_name,
                                    project_info=project_info,
                                    layers_info=layers_info)
        assert layers is not None
        assert len(layers) == 1
        assert type(layers[0]) == DockerBuildLayer
        assert layers[0].registry_config['Host'] == 'quay.io'
        assert layers[0].exposed_ports == [80]

    def test_parse_project_yaml_minimal(self):
        project_name = "flaskexample"
        project_info = {
            'layers': ['app'],
            'app_name': 'flaskexample',
        }
        layers_info = { 'app':
            {
                'info': {
                    'help': 'Build Flask Example app',
                },
                'path': '/'
            }
        }
        layers = parse_project_yaml(project_name=project_name,
                                    project_info=project_info,
                                    layers_info=layers_info)
        assert layers is not None
        assert len(layers) == 1
        assert type(layers[0]) == DockerBuildLayer

    def test_parse_project_yaml_raises_on_missing_layer_help(self):
        project_name = "flaskexample"
        project_info = {
            'layers': ['app'],
            'app_name': 'flaskexample',
        }
        layers_info = {'app': {'info': {}, 'path': '/'}}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_name=project_name,
                               project_info=project_info,
                               layers_info=layers_info)
        assert 'missing a Help' in str(exc_info.value)

    def test_parse_project_yaml_raises_on_missing_project_appname(self):
        project_name = "flaskexample"
        project_info = {
            'layers': ['app'],
        }
        layers_info = {'app': {'info': {'help': "I'm trapped!"}, 'path': '/'}}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_name=project_name,
                               project_info=project_info,
                               layers_info=layers_info)
        assert 'app_name' in str(exc_info.value)
