#!/usr/bin/env python

from __future__ import unicode_literals, absolute_import, print_function

import imp
import os
import sys
import yaml

from .base import BuildLayerBase, FlyingCloudError


def import_class(implementation_filename, base_class):
    impl_dir, impl_filename = os.path.split(implementation_filename)
    module_name, _ = os.path.splitext(impl_filename)

    try:
        sys.path.insert(0, impl_dir)
        fp, filename, description = imp.find_module(module_name)
        module = imp.load_module(module_name, fp, filename, description)
        for name in dir(module):
            obj = getattr(module, name)
            if (type(obj) == type(base_class)
                and issubclass(obj, base_class)
                and obj != base_class):
                    return obj
        raise ValueError("No subclass of {0} in {1}".format(
                base_class.__name__, implementation_filename))
    finally:
        sys.path.pop(0)



def get_layer(layer_base_class, app_name, layer_name, layer_data, registry_config):
    layer_info, layer_path = layer_data["info"], layer_data["path"]
    python_layer_filename = os.path.join(layer_path, "layer.py")
    if os.path.exists(python_layer_filename):
        layer_class = import_class(python_layer_filename, layer_base_class)
    else:
        layer_class = layer_base_class

    parent = layer_info.get("parent")
    source_image_base_name = '{}_{}'.format(app_name, parent) if parent else None
    help = layer_info.get('help')
    if not help:
        raise FlyingCloudError("layer %s is missing a Help string." % layer_name)
    description = layer_info.get('description')
    exposed_ports = layer_info.get('exposed_ports')

    layer = layer_class(
        app_name=app_name,
        layer_name=layer_name,
        source_image_base_name=source_image_base_name,
        help=help,
        description=description,
        exposed_ports=exposed_ports,
        registry_config=registry_config,
    )

#   print(layer.__dict__)

    return layer


def parse_project_yaml(project_name=None, project_info=None, layers_info=None):
    if 'app_name' in project_info:
        app_name = project_info['app_name']
    else:
        raise FlyingCloudError("Missing 'app_name'")

    registry_config = dict()
    if 'registry' in project_info:
        for rk, yk in [
                ('Host', 'host'),
                ('Organization', 'organization'),
                ('RegistryDockerVersion', 'registry_docker_version'),
                ('LoginRequired', 'login_required'),
                ('PullLayer', 'pull_layer'),
                ('PushLayer', 'push_layer'),
                ('SquashLayer', 'squash_layer'),
            ]:
            value = project_info['registry'].get(yk, None)
            if value is not None:
                registry_config[rk] = value

    layers = [get_layer(BuildLayerBase, app_name, layer_name,
                        layers_info[layer_name], registry_config)
              for layer_name in project_info["layers"]]

    return layers


def get_project_info(project_root):
    project_filename = os.path.join(project_root, "flyingcloud.yaml")
    project_name = os.path.basename(project_root)
    with open(project_filename) as fp:
        project_info = yaml.load(fp)

    layers_info = {}
    for layer_name in project_info['layers']:
        layer_path = os.path.join(project_root, "salt", layer_name)
        layer_filename = os.path.join(layer_path, "layer.yaml")
        with open(layer_filename) as fp:
            info = yaml.load(fp)
            layers_info[layer_name] = dict(info=info, path=layer_path)

    return project_name, project_info, layers_info


def configure_layers(project_root):
    project_name, project_info, layers_info = get_project_info(project_root)
    return parse_project_yaml(project_name=project_name,
                              project_info=project_info,
                              layers_info=layers_info)


def main():
    BuildLayerBase.check_root()

    project_root = os.getcwd()
    base_dir = os.path.abspath(project_root)
    defaults = dict(
        base_dir=base_dir,
    )

    try:
        layers = configure_layers(project_root)
        if not layers:
            raise ValueError("Uh!")
    except:
        # TODO: argparse help
        raise

    instance = layers[0]
    instance.check_environment_variables()
    namespace = instance.parse_args(
        defaults,
        *layers,
        description="Build Docker images using SaltStack")

    instance = namespace.layer_inst
    instance.run_build(namespace)
