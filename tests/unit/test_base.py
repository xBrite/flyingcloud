# -*- coding: utf-8 -*-

import os
import yaml

# noinspection PyUnresolvedReferences
import pytest

from flyingcloud.base import DockerBuildLayer


class TestBuildLayer:
    def test_container_ports(self):
        exposed_ports = [443, {'8080': 80}, {1111: [12, '34', 56]}]
        container_ports = DockerBuildLayer.container_ports(exposed_ports)
        assert [443, 80, 12, 34, 56] == container_ports

    def test_host_ports(self):
        exposed_ports = [443, {'8080': 80}, {1111: [12, '34', 56]}]
        host_ports = DockerBuildLayer.host_ports(exposed_ports)
        assert [443, 8080, 1111] == host_ports

    def test_port_bindings(self):
        exposed_ports = [443, {'8080': 80}, {1111: [12, '34', 56]}]
        bindings = DockerBuildLayer.port_bindings(exposed_ports)
        assert {443: 443, 80: 8080, 12: 1111, 34: 1111, 56: 1111} == bindings


    def _make_environment(self, env_var_list, env_config_yaml, os_environ=os.environ):
        try:
            prev_environ, os.environ = os.environ, os_environ
            env_config = yaml.load(env_config_yaml)["environment"]
            return DockerBuildLayer.make_environment(env_var_list, env_config)
        finally:
            os.environ = prev_environ

    def test_make_environment1(self):
        assert dict(
            AWS_ACCESS_KEY_ID="axes_quay",
            AWS_SECRET_ACCESS_KEY="$ekr3t",
            AWS_DEFAULT_REGION="us-east-1",
            INI_FILE="production.ini",
            PARAMS="PATH=/usr/bin HOME=/home/work",
            PIP="/venv/bin/pip",
            USER="fakeroot",
        ) == self._make_environment(
            ["INI_FILE=production.ini",  # override
             "USER=fakeroot",
             "PARAMS=PATH=/usr/bin HOME=/home/work",
             ],
            """\
environment:
  - AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  - AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
  - AWS_DEFAULT_REGION: us-east-1
  - INI_FILE: test.ini
  - PIP: $VIRTUAL_ENV/bin/pip
""",
            os_environ=dict(
                AWS_ACCESS_KEY_ID="axes_quay",
                AWS_SECRET_ACCESS_KEY="$ekr3t",
                VIRTUAL_ENV="/venv",
            )
        )

    def test_make_environment2(self):
        assert dict(
            AWS_ACCESS_KEY_ID="axes_quay",
            AWS_SECRET_ACCESS_KEY="$ekr3t",
            AWS_DEFAULT_REGION="us-east-1",
            INI_FILE="production.ini",
            PIP="/venv/bin/pip",
            USER="fakeroot",
        ) == self._make_environment(
            ["INI_FILE=production.ini",  # override
             "USER=fakeroot"],
            """\
environment:
  AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
  AWS_DEFAULT_REGION: us-east-1
  INI_FILE: test.ini
  PIP: $VIRTUAL_ENV/bin/pip
""",
            os_environ=dict(
                AWS_ACCESS_KEY_ID="axes_quay",
                AWS_SECRET_ACCESS_KEY="$ekr3t",
                VIRTUAL_ENV="/venv",
            )
        )


    def test_parse_docker_login(self):
        args = ["docker", "login", "-u", "ahab", "-p", "CallMeIshmael",
                "-e", "none", "https://whitewhale.com/mobydick"]
        namespace, registry = DockerBuildLayer.parse_docker_login(args)
        assert "ahab" == namespace.username
        assert "CallMeIshmael" == namespace.password
        assert "none" == namespace.email
        assert "https://whitewhale.com/mobydick" == registry

