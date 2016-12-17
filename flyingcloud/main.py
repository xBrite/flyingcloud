#!/usr/bin/env python

from __future__ import unicode_literals, absolute_import, print_function

import os

import sys
import yaml

from .base import DockerBuildLayer, FlyingCloudError
from .utils import import_derived_class


def get_layer(app_name, layer_name, layer_data, registry_config):
    layer_info, layer_path = layer_data["info"], layer_data["path"]
    python_layer_filename = os.path.join(
        layer_path, layer_info.get("code", "layer.py"))
    if os.path.exists(python_layer_filename):
        layer_class = import_derived_class(python_layer_filename, DockerBuildLayer)
    else:
        layer_class = DockerBuildLayer

    parent = layer_info.get("parent")
    source_image_base_name = '{}_{}'.format(app_name, parent) if parent else None
    help = layer_info.get('help')
    if not help:
        raise FlyingCloudError("layer %s is missing a Help string." % layer_name)
    description = layer_info.get('description')
    exposed_ports = layer_info.get('exposed_ports')
    container_name = layer_info.get('image_name')
    environment = layer_info.get('environment')

    layer = layer_class(
        app_name=app_name,
        layer_name=layer_name,
        source_image_base_name=source_image_base_name,
        help=help,
        description=description,
        container_name=container_name,
        exposed_ports=exposed_ports,
        registry_config=registry_config,
        environment=environment,
    )

#   print(layer.__dict__)

    return layer


def parse_project_yaml(project_info, layers_info):
    if 'app_name' in project_info:
        app_name = project_info['app_name']
    else:
        raise FlyingCloudError("Missing 'app_name'")
    if not project_info.get("layers"):
        raise FlyingCloudError("Missing 'layers'")
    project_info.setdefault('description', "Build Docker images using SaltStack")

    registry_config = project_info.get('registry')
    layers = [get_layer(app_name, layer_name, layers_info[layer_name], registry_config)
              for layer_name in project_info["layers"]]
    return layers


def get_project_info(project_root):
    project_config_file = os.path.join(project_root, "flyingcloud.yaml")
    project_info = {}
    if os.path.exists(project_config_file) and os.path.isfile(project_config_file):
        with open(project_config_file) as fp:
            project_info = yaml.load(fp)

    layers_info = {}
    layers = project_info.get('layers', [])
    for layer_name in layers:
        layer_path = os.path.join(project_root, "salt", layer_name)
        layer_filename = os.path.join(layer_path, "layer.yaml")
        with open(layer_filename) as fp:
            info = yaml.load(fp)
            layers_info[layer_name] = dict(info=info, path=layer_path)

    return project_info, layers_info


def configure_layers(project_root):
    project_info, layers_info = get_project_info(project_root)
    layers = None
    if project_info != {}:
        layers = parse_project_yaml(project_info, layers_info)
    return project_info, layers


def main():
    DockerBuildLayer.check_user_is_root()

    project_root = os.path.abspath(os.getcwd())
    defaults = dict(
        base_dir=project_root,
    )

    try:
        project_info, layers = configure_layers(project_root)
    except FlyingCloudError:
        # TODO: argparse help
        raise

    if layers is not None:
        instance = layers[0]
        namespace = instance.parse_args(
            defaults,
            *layers,
            description=project_info['description'])
        instance.check_environment_variables(namespace)

        instance = namespace.layer_inst
        instance.do_operation(namespace)
    else:
        instance = DockerBuildLayer('no_app', 'no_layer', 'no_image_base', "no layer present")
        namespace = instance.parse_args(
            defaults,
            description='** No flyingcloud.yaml found, so no subcommands are available to build layers. Are you in the right directory?')

if __name__ == '__main__':
    main()
