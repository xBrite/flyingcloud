# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections
import fnmatch
import os
import shutil
import errno


def abspath(path):
    return os.path.abspath(os.path.expanduser(path))


def make_dir(target_dir, mode=0o777):
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
