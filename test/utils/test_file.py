# -*- coding: utf-8 -*-

import os
from unittest import TestCase
import mock

from flyingcloud.utils import walk_dir_tree, abspath, PushDir, MockDirWalk

PACKAGE_ROOT = abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
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
                top='.',
                this_file=os.path.join('.', os.path.relpath(THIS_FILE, PACKAGE_ROOT)))

    def test_walk_dir_tree_absolute(self):
        self._test_walk_dir_tree(PACKAGE_ROOT, THIS_FILE)

    def _test_mock_dirwalk(self, dirtree, root, expected):
        walker = MockDirWalk(dirtree)
        result = set(os.path.join(top, f)
            for top, dirs, files in walker(root)
                for f in files)
        self.assertEqual(set([os.path.join(root, e) for e in expected]), result)
        return result

    GreekDirTree = [
        'alpha',
        'beta',
        {
            'gamma' : [
                'delta',
                'epsilon'
            ],
            'zeta' : [
                {
                    'eta': [
                        {
                            'theta': [
                                'iota'
                            ]
                        }
                    ]
                }
            ],
            'kappa' : [],
            'lambda': [
                'mu'
            ]
        }
    ]

    GreekFilenames = [
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
        'quux.mk',
        'zquux.lst',
        {
            'package' : [
                '__init__.py',
                '__init__.pyc',
                {
                    'utils': [
                        'file.py',
                        'context_manager.py'
                    ]
                },
                'foo.py',
                'foo.pyc',
                'bar.py',
                'bar.pyc',
                'protest_something.py',
                'quux.rst'
            ]
        },
        {
            'package.egg-info': [
                'PKG-INFO',
                'SOURCES.txt'
            ]
        },
        {
            'test': [
                'test_foo.py',
                'test_bar.py'
            ]
        },
        'Changelog.txt',
        'setup.py',
        'setup.pyc'
    ]

    PackageFilenames = [
        'LICENSE',
        'README.md',
        'Changelog.txt',
        'setup.py',
        'setup.pyc',
        'quux.mk',
        'zquux.lst',
        'package/__init__.py',
        'package/__init__.pyc',
        'package/bar.py',
        'package/bar.pyc',
        'package/foo.py',
        'package/foo.pyc',
        'package/protest_something.py',
        'package/quux.rst',
        'package/utils/file.py',
        'package/utils/context_manager.py',
        'package.egg-info/PKG-INFO',
        'package.egg-info/SOURCES.txt',
        'test/test_foo.py',
        'test/test_bar.py',
    ]

    def test_mock_dirwalk_relative(self):
        self._test_mock_dirwalk(self.GreekDirTree, '.', self.GreekFilenames)
        self._test_mock_dirwalk(self.PackageDirTree, '.', self.PackageFilenames)

    def test_mock_dirwalk_absolute(self):
        self._test_mock_dirwalk(self.GreekDirTree, '/some/where', self.GreekFilenames)
        self._test_mock_dirwalk(self.PackageDirTree, '/what/ever', self.PackageFilenames)

    def _test_mock_dirwalk_tree(self, dirtree, root, includes, excludes, expected):
        with mock.patch('os.walk', MockDirWalk(dirtree)):
            result = set(walk_dir_tree(root, includes, excludes))
        self.assertEqual(set([os.path.join(root, e) for e in expected]), result)
        return result

    def test_mock_dirwalk_tree_no_filters(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', None, None,
            [f for f in self.PackageFilenames])

    def test_mock_dirwalk_tree_exclude_test(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', None, ['test_*'],
            [f for f in self.PackageFilenames if '/test_' not in f])

    def test_mock_dirwalk_tree_include_py_md(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', ['*.py', '*.md'], None,
            [f for f in self.PackageFilenames
             if (f.endswith('.py') or f.endswith('.md'))])

    def test_mock_dirwalk_tree_include_quux_pyc(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', ['quux*', '*.pyc'], None,
            [f for f in self.PackageFilenames
             if (('/quux' in f or f.startswith('quux'))  or f.endswith('.pyc'))])
        self.assertIn('./quux.mk', result)
        self.assertIn('./package/quux.rst', result)
        self.assertNotIn('./zquux.lst', result)

    def test_mock_dirwalk_tree_include_py_md_exclude_test(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', ['*.py', '*.md'], ['test_*'],
            [f for f in self.PackageFilenames
             if (f.endswith('.py') or f.endswith('.md')) and '/test_' not in f])

    def test_mock_dirwalk_tree_include_py_md_txt_exclude_test_egg_info(self):
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', ['*.py', '*.md', '*.txt'], ['test_*', '*.egg-info'],
            [f for f in self.PackageFilenames
             if (f.endswith('.py') or f.endswith('.md') or f.endswith('.txt'))
             and '/test_' not in f and '.egg-info/' not in f])

    def test_mock_dirwalk_tree_include_py_md_txt_exclude_test_utils_context(self):
        # Check that '/' works in exclude patterns
        result = self._test_mock_dirwalk_tree(
            self.PackageDirTree, '.', ['*.py', '*.md'], ['test_*', 'utils/context_*'],
            [f for f in self.PackageFilenames
             if (f.endswith('.py') or f.endswith('.md'))
                 and '/test_' not in f and 'utils/context_' not in f])
        self.assertIn('./package/utils/file.py', result)
        self.assertNotIn('./package/utils/context_manager.py', result)
