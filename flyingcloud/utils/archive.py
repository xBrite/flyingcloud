# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import logging
import os
import tarfile
import zipfile

from .walk_dir_tree import (
    fnmatch_includes_regex, fnmatch_excludes_regex,
    filter_dirnames, filter_filenames)
from .file import abspath

logger = logging.getLogger(__name__)


def tar_compression_mode(filename):
    if filename.endswith(".tar.gz") or filename.endswith(".tgz"):
        return ":gz"
    elif filename.endswith(".tar.bz2") or filename.endswith(".tbz2"):
        return ":bz2"
    else:
        return ""


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename,
                      "w" + tar_compression_mode(output_filename)) as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def orig_zip_add_directory(
    zip_archive, source_dir,
    exclude_dirs=None, exclude_extensions=None, exclude_filenames=None,
    prefix_dir=None):
    """Recursively add a directory tree to `zip_archive`."""
    exclude_dirs = set(exclude_dirs or ())
    exclude_extensions = set(exclude_extensions or ())
    exclude_filenames = set(exclude_filenames or ())
    relroot = abspath(os.path.join(source_dir, "."))
    logger.info("zip_add_directory: exclude_dirs={!r}, exclude_extensions={!r}, exclude_filenames={!r}".format(
        exclude_dirs, exclude_extensions, exclude_filenames))

    def is_excluded_dirpath(dirpath):
        return any([dirpath.endswith(name) for name in exclude_dirs])

    def is_excluded_dirname(dirname):
        return dirname in exclude_dirs

    def filename_extension_excluded(name):
        return any([name.endswith(ext) for ext in exclude_extensions])

    for dirpath, dirnames, filenames in os.walk(source_dir):
        logger.info("zip: dirpath={0!r}, dirnames={1!r}, filenames={2!r}".format(
            dirpath, dirnames, filenames))

        # Must modify dirnames in-place, per os.walk documentation,
        # to prevent traversal of excluded subdirectories.
        # We must enumerate a copy of `dirnames` as the in-place modifications
        # confuse the iterator.
        for dir in list(dirnames):
            logger.info("zip: Examining dir {0!r}".format(dir))
            if is_excluded_dirname(dir) or is_excluded_dirpath(dirpath) \
                or filename_extension_excluded(dir):
                logger.info("zip: Removing dir {0!r}".format(dir))
                dirnames.remove(dir)
            else:
                logger.info("zip: Retaining dir {0!r}".format(dir))

        files = []

        for filename in filenames:
            if filename in exclude_filenames or filename_extension_excluded(filename):
                logger.info("zip: Removing filename {0!r}".format(filename))
                continue
            else:
                files.append(filename)

        arcdir = os.path.join(
            prefix_dir or '', os.path.relpath(dirpath, relroot))
        zip_write_directory(
            zip_archive, arcdir, dirpath, files)


def zip_add_directory(
        zip_archive, source_dir,
        exclude_dirs=None, exclude_extensions=None, exclude_filenames=None,
        prefix_dir=None):
    """Recursively add a directory tree to `zip_archive`."""
    exclude_dirs = exclude_dirs or []
    exclude_filenames = exclude_filenames or []
    exclude_extensions = ['*'+ext for ext in (exclude_extensions or ())]
    relroot = abspath(os.path.join(source_dir, "."))
    logger.info("zip_add_directory: exclude_dirs={!r}, exclude_extensions={!r}, exclude_filenames={!r}".format(
        exclude_dirs, exclude_extensions, exclude_filenames))
    includes_re = fnmatch_includes_regex(None)
    excludes_re = fnmatch_excludes_regex(
        list(exclude_dirs) + list(exclude_filenames) + list(exclude_extensions))
    logger.debug("excludes_re=%s", excludes_re.pattern)


    for top, dirnames, filenames in os.walk(source_dir, topdown=True):
        logger.debug("zip: top={0!r}, dirnames={1!r}, filenames={2!r}".format(
            top, dirnames, filenames))
        dirnames[:] = filter_dirnames(top, dirnames, excludes_re)
        filenames = filter_filenames(
            top, filenames, includes_re, excludes_re, as_filenames=True)
        logger.debug("zip: >> dirnames={1!r}, filenames={2!r}".format(
            top, dirnames, filenames))
        arcdir = os.path.join(
            prefix_dir or '', os.path.relpath(top, relroot))
        zip_write_directory(
            zip_archive, arcdir, top, filenames)


def zip_write_directory(zip_archive, arcdir, dirpath, filenames):
    if not filenames:
        # add directory `dirpath` (needed for empty dirs)
        logger.debug("zip: Adding dir {0!r} -> {1!r}".format(dirpath, arcdir))
        zip_archive.write(dirpath, arcdir)
    else:
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):  # regular files only
                arcname = os.path.join(arcdir, filename)
                logger.debug("zip: Zipping {0!r} -> {1!r}".format(filepath, arcname))
                zip_archive.write(filepath, arcname)
                # TODO add symlink support, per https://gist.github.com/kgn/610907


def make_zipfile(
        output_filename, source_dir,
        exclude_dirs=None, exclude_extensions=None):
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_add_directory(zip_file, source_dir, exclude_dirs, exclude_extensions)


def check_zipfile(zip_filename):
    if not zipfile.is_zipfile(zip_filename):
        raise Exception('Not a ZIP file')
    with zipfile.ZipFile(zip_filename) as zip_file:
        zip_file.testzip()
        filenames = zip_file.namelist()
        seen = set()
        for filename in filenames:
            if filename in seen:
                raise Exception('Duplicate filename found: {}'.format(filename))
            else:
                seen.add(filename)
