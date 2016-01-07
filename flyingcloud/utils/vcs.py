# -*- coding: utf-8 -*-

"""Simple wrapper around Git and Mercurial."""

from __future__ import absolute_import, print_function

import os
import subprocess

from .process import run_command


class VCS(object):
    def __init__(self, root):
        self.root = root

    def __repr__(self):
        return "<%s root=%r>" % (self.__class__.__name__, self.root)

    @classmethod
    def run_cmd(cls,params, cwd, one_liner=True, *args, **kwargs):
#       print(cls.Executable + params, "cwd=", self.root)
        rv = run_command(cls.Executable + params, cwd=cwd, log_errors=False, *args, **kwargs)
        return rv[0] if rv and one_liner else rv

    def command(self, params, one_liner=True, *args, **kwargs):
        return self.run_cmd(params, cwd=self.root, one_liner=one_liner, *args, **kwargs)


class Git(VCS):
    Executable = ["git"]

    @classmethod
    def find_root(cls, dir):
        try:
            relroot = cls.run_cmd(params=["rev-parse", "--show-cdup"], cwd=dir)
            return os.path.normpath(os.path.join(dir, relroot.strip() or "."))
        except (subprocess.CalledProcessError, OSError):
            return None

    def checkout(self, branch):
        return self.command(["checkout", branch])

    def sha(self):
        return self.command(["rev-parse", "--short", "HEAD"])

    def revision(self):
        return int(self.command(["rev-list", "--count", "HEAD"]))

    def current_branch(self):
        return self.command(["rev-parse", "--abbrev-ref", "HEAD"])

    def branch_exists(self, branch):
        try:
            return self.command(["show-ref", "refs/heads/"+branch])
        except subprocess.CalledProcessError:
            return False


class Mercurial(VCS):
    Executable = ["hg"]

    @classmethod
    def find_root(cls, dir):
        try:
            return cls.run_cmd(["root"], cwd=dir).strip()
        except (subprocess.CalledProcessError, OSError):
            return None

    def checkout(self, branch):
        raise NotImplementedError("checkout")

    def sha(self):
        return self.command(["identify", "--id"])

    def revision(self):
        return int(self.command(["identify", "--num"]))

    def current_branch(self):
        return self.command(["branch"])

    def branch_exists(self, branch):
        raise NotImplementedError("branch_exists")


def find_vcs(dir):
    for vcs in (Git, Mercurial):
        root = vcs.find_root(dir)
        if root:
            return vcs(root)
    return None
