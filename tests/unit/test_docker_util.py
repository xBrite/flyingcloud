# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

# noinspection PyUnresolvedReferences
import pytest
import unittest

from docker.errors import DockerException
from mock import MagicMock
from flyingcloud.utils.docker_util import retry_call


class TestDockerUtils(unittest.TestCase):
    def test_retry_success(self):
        def fn(counter):
            if counter["c"] == 2:
                return "yay"
            counter["c"] += 1
            raise DockerException("fail")

        logger = MagicMock()
        counter = {"c": 0}
        res = retry_call(fn, 'test_retry_success', logger, 3, counter)

        self.assertEqual(res, "yay")
        self.assertEqual(counter["c"], 2)


    def test_retry_failure(self):
        def fn(counter):
            counter["c"] += 1
            raise DockerException("fail")

        logger = MagicMock()
        counter = {"c": 0}

        self.assertRaises(DockerException, retry_call, fn, 'test_retry_failure', logger, 3, counter)
        self.assertEqual(counter["c"], 3)
