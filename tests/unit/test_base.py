# -*- coding: utf-8 -*-

import pytest

from flyingcloud.base import DockerBuildLayer, FlyingCloudError


class TestBuildLayer:
    def test_docker_ports(self):
        exposed_ports = [443, {'80': 8080}]
        docker_ports = DockerBuildLayer.docker_ports(exposed_ports)
        assert [443, 80] == docker_ports

    def test_host_ports(self):
        exposed_ports = [443, {'80': '8080'}]
        host_ports = DockerBuildLayer.host_ports(exposed_ports)
        assert [443, 8080] == host_ports

