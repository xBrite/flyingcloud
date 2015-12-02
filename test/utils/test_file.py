# -*- coding: utf-8 -*-

import os
from unittest import TestCase

from flyingcloud.utils import walk_tree, abspath, ChDir

PACKAGE_ROOT = abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
THIS_FILE = os.path.splitext(__file__)[0] + '.py'  # Otherwise, sometimes ends in '.pyc'

class TestFileUtils(TestCase):
    def _test_walk_tree(self, top, this_file):
        files = set(walk_tree(top, ('*.py', '*.md'),
                              ('test*.py', '__init__.py', '.git')))
        self.assertNotIn(this_file, files)
        files = set(walk_tree(top, ('*.py', '*.md')))
        self.assertIn(this_file, files)

    def test_walk_tree_relative(self):
        with ChDir(PACKAGE_ROOT):
            self._test_walk_tree(
                ".",
                os.path.join(".", os.path.relpath(THIS_FILE, PACKAGE_ROOT)))

    def test_walk_tree_absolute(self):
        self._test_walk_tree(PACKAGE_ROOT, THIS_FILE)
