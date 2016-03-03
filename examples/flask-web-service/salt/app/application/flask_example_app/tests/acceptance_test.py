#!/usr/bin/env python

# -*- coding: utf-8 -*-

import os
import unittest
import requests


class AppAcceptanceTests(unittest.TestCase):
    APP_PORT = os.environ.get('APP_PORT', 80)
    def test_canny(self):
        r = requests.get("http://localhost:{}/canny".format(self.APP_PORT))
        r.raise_for_status()


if __name__ == '__main__':
    unittest.main()
