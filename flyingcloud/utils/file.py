# -*- coding: utf-8 -*-

from __future__ import absolute_import

import fnmatch
import os
import shutil
import errno


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
