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
    return walk_dir_tree_regex(
        root,
        fnmatch_includes_regex(includes),
        fnmatch_excludes_regex(excludes))


def fnmatch_includes_regex(includes=None):
    # Transform glob patterns to regular expressions
    return re.compile(
        '|'.join([fnmatch.translate(x) for x in includes])
        if includes else '.*')


def fnmatch_excludes_regex(excludes=None):
    return re.compile(
        '(^|/)' + '|'.join([fnmatch.translate(x) for x in excludes])
        if excludes else '$.')


def walk_dir_tree_regex(root, includes_re, excludes_re):
    for top, dirnames, filenames in os.walk(root, topdown=True):
        # exclude directories by mutating `dirnames`
        dirnames[:] = filter_dirnames(top, dirnames, excludes_re)
        for pathname in filter_filenames(
                top, filenames, includes_re, excludes_re, as_filenames=False):
            yield pathname


def filter_dirnames(top, dirnames, excludes_re):
    return [
        d for d in dirnames
            if not excludes_re.search(os.path.join(top, d))]


def filter_filenames(top, filenames, includes_re, excludes_re, as_filenames=True):
    result = []
    for filename in filenames:
        if includes_re.match(filename):
            pathname = os.path.join(top, filename)
            if not excludes_re.search(pathname):
                result.append(filename if as_filenames else pathname)
    return result


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
