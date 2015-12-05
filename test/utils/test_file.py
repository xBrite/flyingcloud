# -*- coding: utf-8 -*-

import os
from unittest import TestCase

from flyingcloud.utils import walk_tree, abspath, PushDir, MockWalk

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
        with PushDir(PACKAGE_ROOT):
            self._test_walk_tree(
                ".",
                os.path.join(".", os.path.relpath(THIS_FILE, PACKAGE_ROOT)))

    def test_walk_tree_absolute(self):
        self._test_walk_tree(PACKAGE_ROOT, THIS_FILE)

    def test_mock_walk(self):
        dirtree = [
            'LICENSE',
            'README.md',
            {
                'package' : [
                    '__init__.py',
                    {
                        'utils': [
                            'file.py',
                            'context_manager.py'
                        ]
                    },
                    'foo.py'
                ]
            },
            {
                'package.egg-info': [
                    'PKG-INFO',
                    'SOURCES.txt'
                ]
            },
            'setup.py'
        ]
        walker = MockWalk(dirtree)
        result = set()
        for top, dirs, files in walker('/what/ever'):
            for f in files:
                result.add(os.path.join(top, f))
        self.assertEqual(
            result,
            set([
                "/what/ever/LICENSE",
                "/what/ever/README.md",
                "/what/ever/setup.py",
                "/what/ever/package/__init__.py",
                "/what/ever/package/foo.py",
                "/what/ever/package/utils/file.py",
                "/what/ever/package/utils/context_manager.py",
                "/what/ever/package.egg-info/PKG-INFO",
                "/what/ever/package.egg-info/SOURCES.txt"
            ]))




