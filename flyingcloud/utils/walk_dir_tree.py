# -*- coding: utf-8 -*-

import fnmatch
import os
import re


def walk_dir_tree(root, includes=None, excludes=None):
    """Walk and filter a directory tree by wildcards.

    :param includes: A list of file wildcards to include.
        If `None`, then all files are (potentially) included.
    :param excludes: A list of file and directory wildcards to exclude.
        If `None`, then no files or directories are excluded.

    Adapted (and fixed!) from http://stackoverflow.com/a/5141829/6364
    """
    # Transform glob patterns to regular expressions
    includes_re = re.compile(
        '|'.join([fnmatch.translate(x) for x in includes])
        if includes else '.*')
    excludes_re = re.compile(
        '(^|/)' + '|'.join([fnmatch.translate(x) for x in excludes])
        if excludes else '$.')

    for top, dirnames, filenames in os.walk(root, topdown=True):
        # exclude directories by mutating `dirnames`
        dirnames[:] = [
            d for d in dirnames
            if not excludes_re.search(os.path.join(top, d))]
        # filter filenames
        pathnames = [os.path.join(top, f) for f in filenames
                     if includes_re.match(f)]
        pathnames = [p for p in pathnames if not excludes_re.search(p)]

        for p in pathnames:
            yield p


class MockDirWalk:
    """Mock implementation of os.walk."""
    def __init__(self, dirtree):
        self.dirtree = dirtree

    def __call__(self, top, topdown=True, onerror=None, followlinks=False):
        """Emulate os.walk with `self.dirtree`"""
        return self.walk(self.dirtree, top, topdown)

    def walk(self, dirlist, top, topdown):
        dirnames, filenames, dirmap = [], [], {}
        for node in dirlist:
            if isinstance(node, dict):
                for name, subdir in node.items():
                    dirnames.append(name)
                    dirmap[name] = subdir
            else:
                filenames.append(node)

        if topdown:
            yield top, dirnames, filenames
        for name in dirnames:
            for t,d,f in self.walk(dirmap[name], os.path.join(top, name), topdown):
                yield t,d,f
        if not topdown:
            yield top, dirnames, filenames
