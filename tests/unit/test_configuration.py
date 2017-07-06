# -*- coding: utf-8 -*-
import os

import pytest

from flyingcloud import DockerBuildLayer, FlyingCloudError
from flyingcloud.main import parse_project_yaml, configure_layers


class TestConfiguration:
    def test_parse_yaml(self, tmpdir):
        salt_dir = tmpdir.mkdir("salt")
        project_file = tmpdir.join("flyingcloud.yaml")
        project_file_content = """\
app_name: 'flaskexample'
layers:
  - app
registry:
    host: quay.io
    organization: cookbrite
    registry_docker_version: "1.17"
    login_required: false
    pull_layer: false
    push_layer: false
    squash_layer: false
        """
        project_file.write(project_file_content)
        app_dir = salt_dir.mkdir("app")
        layer_file = app_dir.join("layer.yaml")
        layer_file_content = """\
help: Build Flask Example app
parent: opencv
exposed_ports:
  - 80
  - 443
        """
        layer_file.write(layer_file_content)
        project_info, layers = configure_layers(str(tmpdir.realpath()))
        assert project_info is not None
        assert layers
        assert len(layers) == 1
        the_layer = layers[list(layers.keys())[0]]
        assert the_layer.exposed_ports == [80, 443]

    def test_parse_project_yaml(self):
        project_info = {
            'app_name': 'flaskexample',
            'layers': ['app'],
            'registry' : {
                'host': 'quay.io',
                'organization': 'cookbrite',
                'registry_docker_version': "1.17",
                'login_required': False,
                'pull_layer': False,
                'push_layer': False,
                'squash_layer': False,
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
        layers = parse_project_yaml(project_info, layers_info)
        assert layers is not None
        assert len(layers) == 1
        the_layer = layers[list(layers.keys())[0]]
        assert type(the_layer) == DockerBuildLayer
        assert the_layer.registry_config['host'] == 'quay.io'
        assert the_layer.exposed_ports == [80]

    def test_parse_project_yaml_minimal(self):
        project_info = {
            'app_name': 'flaskexample',
            'layers': ['app'],
        }
        layers_info = { 'app':
            {
                'info': {
                    'help': 'Build Flask Example app',
                },
                'path': '/'
            }
        }
        layers = parse_project_yaml(project_info, layers_info)
        assert layers is not None
        assert len(layers) == 1
        assert type(layers[list(layers.keys())[0]]) == DockerBuildLayer

    def test_parse_project_yaml_raises_on_missing_layer_help(self):
        project_info = {
            'app_name': 'flaskexample',
            'layers': ['app'],
        }
        layers_info = {'app': {'info': {}, 'path': '/'}}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_info, layers_info)
        assert 'missing a Help' in str(exc_info.value)

    def test_parse_project_yaml_raises_on_missing_project_appname(self):
        project_info = {
            'layers': ['app'],
        }
        layers_info = {}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_info, layers_info)
        assert 'app_name' in str(exc_info.value)

    def test_parse_project_yaml_raises_on_missing_project_layers(self):
        project_info = {
            'app_name': 'someapp'
        }
        layers_info = {}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_info, layers_info)
        assert 'layers' in str(exc_info.value)

    def test_parse_project_yaml_raises_on_empty_project_layers(self):
        project_info = {
            'app_name': 'someapp',
            'layers': [],
        }
        layers_info = {}
        with pytest.raises(FlyingCloudError) as exc_info:
            parse_project_yaml(project_info, layers_info)
        assert 'layers' in str(exc_info.value)
