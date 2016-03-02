# -*- coding: utf-8 -*-
import os

from flyingcloud.main import get_project_info


class TestConfiguration:
    # def test_some_interaction(monkeypatch):
    #     monkeypatch.setattr(os, "getcwd", lambda: "/")

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

