# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

from flyingcloud import BuildLayerBase


class TestRunner(BuildLayerBase):
    def build(self, namespace):
        namespace.logger.info("Hello from TestRunner")
