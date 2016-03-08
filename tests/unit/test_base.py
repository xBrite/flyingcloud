# -*- coding: utf-8 -*-

import pytest

from flyingcloud.base import DockerBuildLayer, FlyingCloudError


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

