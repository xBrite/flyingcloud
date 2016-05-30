.. _installing:

Installing FlyingCloud
======================

FlyingCloud is a Python module, and works under Python 2.7, 3.4, and 3.5.
Installing into a `Python virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_
is recommended.

1. Install Docker
  - Linux

    - `Install Docker <https://docs.docker.com/linux/step_one/>`_

  - Mac OS X

    - Install `Docker Toolbox <https://www.docker.com/products/docker-toolbox>`_ *or*
      `Docker for Mac (beta) <https://beta.docker.com/docs/>`_.
      If you are using Docker for Mac,
      be sure to use the ``-m`` (``--no-use-docker-machine``) flag
      on all ``flyingcloud`` invocations.

  - Windows

    - Not currently supported — send us a pull request if you get it to work!

2. Install `docker-squash <https://github.com/jwilder/docker-squash>`_ (optional) -
   This utility is used to compress Docker filesystem layers into one layer, making http
   data transfer more reliable in some cases.
   **Note**: docker-squash does *not* work with Docker 1.10+
3. Install FlyingCloud

::

    pip install flyingcloud
