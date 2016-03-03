# -*- coding: utf-8 -*-

from unittest import TestCase

from flask_example_app import app


class AppUnitTests(TestCase):
    def test_is_debug_app(self):
        self.assertTrue(app.app.config['DEBUG'])
