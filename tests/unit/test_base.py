# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

import os
import yaml

# noinspection PyUnresolvedReferences
import pytest

from flyingcloud.base import DockerBuildLayer as DBL


class TestBuildLayer:
    def test_parse_exposed_ports_mixed_list(self):
        exposed_ports = [443, {'8080': 80}, {1111: [12, '34', 56]}]
        bindings = DBL.port_bindings(exposed_ports)
        assert {443: 443,  80: 8080,  12: 1111,  34: 1111,  56: 1111} == bindings
        assert {443, 8080, 1111} == set(DBL.host_ports(exposed_ports))
        assert {443, 80, 12, 34, 56} == set(DBL.container_ports(exposed_ports))

    def test_parse_exposed_ports_yaml_dict_of_list_of_one_element_dicts(self):
        exposed_ports = yaml.load("""
exposed_ports:
  # host_port: container_port(s)
  - 443
  - 8080: 80
  - 1111: [12, 34, 56]""")["exposed_ports"]
        bindings = DBL.port_bindings(exposed_ports)
        assert {443: 443,  80: 8080,  12: 1111,  34: 1111,  56: 1111} == bindings
        assert {443, 8080, 1111} == set(DBL.host_ports(exposed_ports))
        assert {443, 80, 12, 34, 56} == set(DBL.container_ports(exposed_ports))

    def test_parse_exposed_ports_yaml_dict(self):
        exposed_ports = yaml.load("""
exposed_ports:
  443: 443
  8080: 80
  1111: [12, 34, 56]""")["exposed_ports"]
        bindings = DBL.port_bindings(exposed_ports)
        assert {443: 443,  80: 8080,  12: 1111,  34: 1111,  56: 1111} == bindings
        assert {443, 8080, 1111} == set(DBL.host_ports(exposed_ports))
        assert {443, 80, 12, 34, 56} == set(DBL.container_ports(exposed_ports))

    def _make_environment(self, env_var_list, env_config_yaml, os_environ=os.environ):
        try:
            prev_environ, os.environ = os.environ, os_environ
            env_config = yaml.load(env_config_yaml)["environment"]
            return DBL.make_environment(env_var_list, env_config)
        finally:
            os.environ = prev_environ

    def test_make_environment1(self):
        config_yamls = [
            """\
            environment:
              - AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
              - AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
              - AWS_DEFAULT_REGION: us-east-1
              - INI_FILE: test.ini
              - PIP: $VIRTUAL_ENV/bin/pip
            """,
            """\
            environment:
              AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
              AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
              AWS_DEFAULT_REGION: us-east-1
              INI_FILE: test.ini
              PIP: $VIRTUAL_ENV/bin/pip
            """,
        ]
        for cy in config_yamls:
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
                env_config_yaml=cy,
                os_environ=dict(
                    AWS_ACCESS_KEY_ID="axes_quay",
                    AWS_SECRET_ACCESS_KEY="$ekr3t",
                    HOME="/home/work",  # unused
                    PATH="/garden:/gnome/3",  # unused
                    VIRTUAL_ENV="/venv",
                )
            )

    def test_make_environment_fails(self):
        config_yamls = [
            """\
            environment:
              - AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
              - AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
            """,
            """\
            environment:
              - FOO: $BAR
            """,
            """\
            environment:
              - FOO:
            """,
        ]
        for cy in config_yamls:
            with pytest.raises(ValueError):
                self._make_environment(
                    [],
                    env_config_yaml=cy,
                    os_environ=dict(
                        AWS_ACCESS_KEY_ID="axes_quay",
                    )
                )

    def test_parse_docker_login(self):
        args = ["docker", "login", "-u", "ahab", "-p", "CallMeIshmael",
                "-e", "none", "https://whitewhale.com/mobydick"]
        namespace, registry = DBL.parse_docker_login(args)
        assert "ahab" == namespace.username
        assert "CallMeIshmael" == namespace.password
        assert "none" == namespace.email
        assert "https://whitewhale.com/mobydick" == registry

    def test_filter_stream_header(self):
        assert (b"""decorator 4.0.11 is already the active version in easy-install.pth""", 1) == DBL.filter_stream_header(
            b"""decorator 4.0.11 is already th\x01\x00\x00\x00\x00\x00 \x00e active version in easy-install.pth""")
        assert (b"Constructing docker client object with {u'version': '1.17', 'timeout': 300}", 0) == DBL.filter_stream_header(
            b"Constructing docker client object with {u'version': '1.17', 'timeout': 300}")
