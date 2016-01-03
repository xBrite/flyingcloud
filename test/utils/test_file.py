# -*- coding: utf-8 -*-

import os
from unittest import TestCase
import mock

from flyingcloud.utils import walk_dir_tree, abspath, PushDir, MockDirWalk

PACKAGE_ROOT = abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
THIS_FILE = os.path.splitext(__file__)[0] + '.py'  # Otherwise, sometimes ends in '.pyc'


class TestFileUtils(TestCase):
    def _test_walk_dir_tree(self, top, this_file):
        # Walk a real file tree
        files = set(walk_dir_tree(top, ('*.py', '*.md'),
                                  ('test*.py', '__init__.py', '.git')))
        self.assertNotIn(this_file, files)
        files = set(walk_dir_tree(top, ('*.py', '*.md')))
        self.assertIn(this_file, files)

    def test_walk_dir_tree_relative(self):
        with PushDir(PACKAGE_ROOT):
            self._test_walk_dir_tree(
                top=".",
                this_file=os.path.join(".", os.path.relpath(THIS_FILE, PACKAGE_ROOT)))

    def test_walk_dir_tree_absolute(self):
        self._test_walk_dir_tree(PACKAGE_ROOT, THIS_FILE)

    def _test_mock_dirwalk(self, dirtree, root, expected):
        walker = MockDirWalk(dirtree)
        result = set(os.path.join(top, f)
            for top, dirs, files in walker(root)
                for f in files)
        self.assertEqual(set([os.path.join(root, e) for e in expected]), result)

    GreekDirTree = [
        'alpha',
        'beta',
        {'gamma' : [ 'delta', 'epsilon'],
         'zeta' : [{'eta': [{'theta': ['iota']}]}],
         'kappa' : [],
         'lambda': ['mu']
         }
    ]

    GreekExpected = [
        'alpha',
        'beta',
        'gamma/delta',
        'gamma/epsilon',
        'zeta/eta/theta/iota',
        'lambda/mu'
    ]

    PackageDirTree = [
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
                'foo.py',
                'bar.py'
            ]
        },
        {
            'package.egg-info': [
                'PKG-INFO',
                'SOURCES.txt'
            ]
        },
        'Changelog.txt',
        'setup.py'
    ]

    PackageExpected = [
        "LICENSE",
        "README.md",
        "Changelog.txt",
        "setup.py",
        "package/__init__.py",
        "package/bar.py",
        "package/foo.py",
        "package/utils/file.py",
        "package/utils/context_manager.py",
        "package.egg-info/PKG-INFO",
        "package.egg-info/SOURCES.txt"
    ]

    def test_mock_dirwalk_relative(self):
        self._test_mock_dirwalk(self.GreekDirTree, '.', self.GreekExpected)
        self._test_mock_dirwalk(self.PackageDirTree, '.', self.PackageExpected)

    def test_mock_dirwalk_absolute(self):
        self._test_mock_dirwalk(self.GreekDirTree, '/some/where', self.GreekExpected)
        self._test_mock_dirwalk(self.PackageDirTree, '/what/ever', self.PackageExpected)

    def _test_mock_dirwalk_tree(self, dirtree, root, includes, excludes, expected):
        with mock.patch('os.walk', MockDirWalk(dirtree)):
            result = set(walk_dir_tree(root, includes, excludes))
        self.assertEqual(set([os.path.join(root, e) for e in expected]), result)

    def test_mock_dirwalk_tree1(self):
        dirtree = ['foo.py', 'foo.pyc', 'test_foo.py', 'foobar.md',
                   {'quux': ['bar.py', 'testbar.py']},
                   {'test_me': ['README.md']}]
        expected = ['foo.py', 'foobar.md', 'quux/bar.py', 'quux/testbar.py']
        self._test_mock_dirwalk_tree(dirtree, '.', ['*.py', '*.md'], ['test_*'], expected)

    def test_mock_dirwalk_tree2(self):
        dirtree = ['foo.py', 'foo.pyc', 'test_foo.py', 'foobar.md',
                   {'quux': ['bar.py', 'testbar.py', {
                       'test_me': ['README.md'],
                       'stuff': ['Nonsense.md']
                   }] }]
        expected = ['foo.py', 'foobar.md', 'quux/bar.py', 'quux/testbar.py', 'quux/stuff/Nonsense.md']
        self._test_mock_dirwalk_tree(dirtree, '.', ['*.py', '*.md'], ['test_*'], expected)
