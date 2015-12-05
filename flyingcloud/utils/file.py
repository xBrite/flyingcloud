# -*- coding: utf-8 -*-

from __future__ import absolute_import

import errno
import fnmatch
import os
import re
import shutil


def abspath(path):
    return os.path.abspath(os.path.expanduser(path))


def make_dir(target_dir, mode=0777):
    """Create (if needed) a directory with a certain file mode."""
    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            raise ValueError("'%s' is not a directory" % target_dir)
        os.chmod(target_dir, mode)
    else:
        try:
            os.makedirs(target_dir, mode)
        except OSError as e:
            # Handle race condition of simultaneous dir creation
            if e.errno != errno.EEXIST:
                raise


def move_file_to_dir(source_file, target_dir, target_basename=None):
    make_dir(target_dir)
    target_dir = abspath(target_dir)
    target_file = os.path.join(
        target_dir, target_basename or os.path.basename(source_file))
    if os.path.exists(target_file):
        os.remove(target_file)
    shutil.move(source_file, target_file)
    return target_file


def find_in_path(command):
    for p in os.getenv("PATH").split(os.pathsep):
        f = os.path.join(p, command)
        if os.path.exists(f):
            return f

def find_recursive_pattern(base_dir, pattern):
    for root, dirnames, filenames in os.walk(base_dir):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def walk_tree(dir, includes, excludes=None):
    """Walk a directory tree, including and excluding files and dirs by wildcards.

    Adapted (and fixed!) from http://stackoverflow.com/a/5141829/6364
    """
    # Transform glob patterns to regular expressions
    includes_re = re.compile('|'.join([fnmatch.translate(x)
                                       for x in includes]))
    excludes_re = re.compile('|'.join([fnmatch.translate(x)
                                       for x in excludes])
                             if excludes else '$.')

    for top, dirs, files in os.walk(dir, topdown=True):
        # exclude directories by mutating `dirs`
        dirs[:] = [d for d in dirs
                   if not excludes_re.search(os.path.join(top, d))]

        # exclude/include files
        files = [os.path.join(top, f) for f in files]
        files = [f for f in files if not excludes_re.search(f)]
        files = [f for f in files if includes_re.search(f)]

        for fname in files:
            yield fname

