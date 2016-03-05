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



def get_layer(layer_base_class, layer_name, layer_data):
    layer_info, layer_path = layer_data["info"], layer_data["path"]
    python_layer_filename = os.path.join(layer_path, "layer.py")
    if os.path.exists(python_layer_filename):
        layer_class = import_class(python_layer_filename, BuildLayerBase)
    else:
        layer_class = layer_base_class
    layer = layer_class(layer_base_class.AppName, command_name=layer_name)
    layer.__doc__ = "Parsed from {}".format(layer_name)
    layer.Description = layer_info.get('description')
    if not layer.Description:
        raise FlyingCloudError("layer %s is missing a description." % layer_name)
    layer.ExposedPorts = layer_info.get('exposed_ports')
    parent = layer_info.get("parent")
    if parent:
        layer.SourceImageBaseName = '{}_{}'.format(
            layer_class.AppName, parent)
    layer.set_layer_defaults()
#   print(layer.__dict__)

    return layer


def parse_project_yaml(project_name=None, project_info=None, layers_info=None):
    BuildLayerBase.project_filename = project_name
    BuildLayerBase.USERNAME_VAR = project_info.get('username_varname', BuildLayerBase.USERNAME_VAR)
    BuildLayerBase.PASSWORD_VAR = project_info.get('password_varname', BuildLayerBase.PASSWORD_VAR)
    BuildLayerBase.Registry = project_info.get('registry', BuildLayerBase.Registry)
    BuildLayerBase.RegistryDockerVersion = project_info.get('registry_docker_version', BuildLayerBase.RegistryDockerVersion)
    BuildLayerBase.Organization = project_info.get('organization', BuildLayerBase.Organization)
    BuildLayerBase.AppName = project_info.get('app_name', BuildLayerBase.AppName)
    BuildLayerBase.LoginRequired = project_info.get('login_required', BuildLayerBase.LoginRequired)
    BuildLayerBase.SquashLayer = project_info.get('squash_layer', BuildLayerBase.SquashLayer)
    BuildLayerBase.PushLayer = project_info.get('push_layer', BuildLayerBase.PushLayer)
    BuildLayerBase.PullLayer = project_info.get('pull_layer', BuildLayerBase.PullLayer)

    layers = []
    for layer_name in project_info["layers"]:
        layers.append(get_layer(BuildLayerBase, layer_name, layers_info[layer_name]))

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
