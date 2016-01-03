# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections
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


# disk_usage: Adapted from http://code.activestate.com/recipes/577972-disk-usage/
if hasattr(shutil, 'disk_usage'):
    # Python >= 3.3
    disk_usage = shutil.disk_usage

elif hasattr(os, 'statvfs'):
    # Posix
    _ntuple_diskusage = collections.namedtuple('usage', 'total used free')

    def disk_usage(path):
        """Return disk usage statistics about the given path.

        Returned value is a named tuple with attributes 'total', 'used' and
        'free', which are the amount of total, used and free space, in bytes.
        """
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return _ntuple_diskusage(total, used, free)

else:
    # There is a Windows implementation in the recipe
    def disk_usage(path):
        raise NotImplementedError("disk_usage not supported")


def walk_dir_tree(root, includes, excludes=None):
    """Walk a directory tree, excluding dirs by wildcards
    and including and excluding files by wildcards.

    Adapted (and fixed!) from http://stackoverflow.com/a/5141829/6364
    """
    # Transform glob patterns to regular expressions
    includes_re = re.compile(
        '|'.join([fnmatch.translate(x) for x in includes]))
    excludes_re = re.compile(
        '|'.join([fnmatch.translate(x) for x in excludes])
        if excludes else '$.')

    for top, dirnames, filenames in os.walk(root, topdown=True):
        # exclude directories by mutating `dirnames`
        dirnames[:] = [
            d for d in dirnames
                if not excludes_re.search(os.path.join(top, d))]

        # exclude/include filenames
        filenames = [os.path.join(top, f) for f in filenames]
        filenames = [f for f in filenames if not excludes_re.search(f)]
        filenames = [f for f in filenames if includes_re.search(f)]

        for f in filenames:
            yield f


class MockDirWalk:
    """Mock implementation of os.walk."""
    def __init__(self, dirtree):
        self.dirtree = dirtree

    def __call__(self, top, topdown=True, onerror=None, followlinks=False):
        "Emulate os.walk with `self.dirtree`"
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
