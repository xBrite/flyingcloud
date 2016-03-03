#!/usr/bin/env python

# -*- coding: utf-8 -*-

import os
import urlparse

import unittest
import requests


class AppAcceptanceTests(unittest.TestCase):
    APP_PORT = os.environ.get('APP_PORT', 80)
    BASE_URL = os.environ.get('BASE_URL', "http://localhost:{}/".format(APP_PORT))

    def test_canny(self):
        canny_url = urlparse.urljoin(self.BASE_URL, "/canny")
        r = requests.get(canny_url)
        r.raise_for_status()


if __name__ == '__main__':
    unittest.main()
