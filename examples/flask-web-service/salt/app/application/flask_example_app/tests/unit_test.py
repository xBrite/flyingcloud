#!/usr/bin/env python

# -*- coding: utf-8 -*-

import unittest

from flask_example_app import app


class AppUnitTests(unittest.TestCase):
    def test_is_debug_app(self):
        self.assertTrue(app.app.config['DEBUG'])


if __name__ == '__main__':
    unittest.main()
