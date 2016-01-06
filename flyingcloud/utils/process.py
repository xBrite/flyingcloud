# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import logging
import os
import subprocess


DevNull = os.open(os.devnull, os.O_RDWR)


class CalledProcessError(subprocess.CalledProcessError):
    def __init__(self, returncode, cmd, output=None):
        super(CalledProcessError, self).__init__(returncode, cmd, output)
        self.cwd = os.getcwd()
    def __str__(self):
        return "Command '%s' (working dir: '%s') returned non-zero exit status %d" % (
            self.cmd, self.cwd, self.returncode)


def run_command_using_sh(cmd, env, kwargs):
    "install the sh module in the system Python to have better debugging of CbCommon module installation (pip install sh)"
    import sh
    command_stdout = ''
    command_stderr = ''
    current_working_directory = kwargs.get('cwd')
    executable_file = cmd[0]
    command_args = cmd[1:]
    command_runner = sh.Command(executable_file)
    try:
        output = command_runner(*command_args, _cwd=current_working_directory, _env=env, _out=command_stdout)
        retcode = output.exit_code
    except sh.ErrorReturnCode as e:
        print("sh e.stderr:{}".format(e.stderr))
        retcode = 1
        command_stderr = e.stderr
        print("command STDOUT:{}".format(command_stdout))
        print("command STDOUT:{}".format(command_stderr))
    return command_stderr, command_stdout, retcode


def run_command_using_popen(cmd, env, kwargs):
    child = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env,
        **kwargs)
    (command_stdout, command_stderr) = child.communicate()
    retcode = child.wait()
    return command_stderr, command_stdout, retcode


def run_command(
        cmd, env=os.environ,
        logger=None, loggerName=None, log_errors=True,
        **kwargs):
    """
    Run the given command, possibly modifying it by inserting some
    convenient options, with the given environment.  Returns an array
    of lines from stdout on success; raises a
    CalledProcessError on failure.
    """
    logger = logger or logging.getLogger(loggerName)

    # Ignore these passed-in keywords: we know better.
    kwargs = kwargs.copy()
    for kw in ['stdout', 'stderr', 'universal_newlines', 'env']:
        if kw in kwargs:
            if log_errors:
                logger.warn("run_command: Ignoring keyword %s", kw)
            del kwargs[kw]

    command_stderr, command_stdout, retcode = run_command_using_popen(cmd, env, kwargs)

    if retcode != 0:
        for line in command_stderr.splitlines():
            if log_errors:
                logger.error("%s", line)
            else:
                logger.debug("%s", line)
        raise CalledProcessError(retcode, cmd)

    rv = command_stdout.splitlines() + command_stderr.splitlines()

    logger.debug("in %s, %s => %s",
                 kwargs.get('cwd', os.getcwd()),
                 cmd, rv)
    # TODO: return (retcode, stdout, stderr)
    return rv
