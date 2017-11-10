# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

from time import sleep
from docker.errors import APIError, DockerException
from .. import exceptions


def retry_call(call, name, logger, retries, *args, **kwargs):
    """ call a function call(), retries times, with *args and **kwargs, and with
    exponential backoff on failure.  if it fails after after retries time, raise
    the last exception """
    exc = None
    for i in range(retries):
        try:
            logger.info("calling %r, attempt %d/%d", name, i+1, retries)
            return call(*args, **kwargs)

        except (APIError, DockerException, exceptions.DockerResultError) as exc:
            logger.exception("error calling %r, retrying", call)
            sleep(2 ** i)

    logger.error("failed calling %r after %d tries, giving up", call,
            retries)
    raise exc
