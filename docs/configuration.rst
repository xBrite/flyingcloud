.. _configuration:

Configuring FlyingCloud
=======================


Project Layout
--------------

Create directories that define your project — each layer will have its own subdirectory:

::

    flask-web-app/
        app/
        opencv/
        pybase/
        sysbase/

``flask-web-app/`` is the project directory.
This is where the ``flyingcloud.yaml`` project definition file goes.

Project Definition — flyingcloud.yaml
-------------------------------------

Example ``flyingcloud.yaml``:

.. code-block:: yaml

    app_name: 'flaskexample'
    description: 'Sample Flask App for FlyingCloud'
    layers:
      - testrunner
      - app
      - opencv
      - pybase
      - sysbase

    registry:
      host: quay.io
      organization: cookbrite
      docker_api_version: "1.17"
      login_required: false
      pull_layer: false
      push_layer: false
      squash_layer: false


Layer Definition Using a Dockerfile
-----------------------------------

Each subdirectory holds files related to that layer as well as a ``layer.yaml``
that defines the layer.

The first layer is usually a "base" layer that will install Salt,
perhaps install some other debugging tools,
and configure Salt to *fail hard* if any state fails.
Fail-hard is not the default for usign Salt in production,
as Salt usually wants to configure servers on a "best-effort" basis
and go on with the rest of the configuration if something fails.

But in a build system, we don't want this to happen,
so we configure Salt to fail-hard.

Example ``layer.yaml`` that for a base layer that builds a Dockerfile:

.. code-block:: yaml

    help: Operating System Base Layer
    description: >
      System base layer
      (Phusion Ubuntu 14.04 with Salt, build-essential,
      various debugging tools)

The only other file in this directory would be the Dockerfile:

.. code-block:: dockerfile

    FROM phusion/baseimage:0.9.18
    MAINTAINER MetaBrite, Inc.
    CMD ["/sbin/my_init"]
    RUN apt-get update
    RUN apt-get install -y tar git vim nano wget net-tools build-essential salt-minion

    # SaltStack fail hard if any state fails
    RUN echo "failhard: True" >> /etc/salt/minion

    # Clean up APT when done.
    RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

This Docker layer installs Salt and some debugging tools.

Telling Salt to Fail Hard
-------------------------

Note the line of the file
``RUN echo "failhard: True" >> /etc/salt/minion``.
This is very important.
It tells SaltStack to fail the build if any Salt states failed.

**You will need this line (or its equivalent) in all your base layers.**


Layer Definition Using Salt States
----------------------------------

Example ``layer.yaml`` that builds on the previous layers -

.. code-block:: yaml

    help: Python 2.7.x Layer
    description: >
      Python base layer with recent 2.7.x version
      (also creates virtualenv at /venv/)
    parent: sysbase

``pybase`` layer's ``top.sls`` file:

.. code-block:: yaml

    base:
      '*':
        - python27-update

``pybase`` layer's ``python-update.sls`` file:

.. code-block:: yaml

    python-software-properties:
      pkg.installed:
        - fromrepo: trusty
        - pkgs:
          - python-software-properties

    # https://launchpad.net/~fkrull/+archive/ubuntu/deadsnakes-python2.7
    python2.7-ppa:
      pkgrepo.managed:
        - humanname: Python 2.7 updates PPA
        - name: deb http://ppa.launchpad.net/fkrull/deadsnakes-python2.7/ubuntu trusty main
        - dist: trusty
        - file: /etc/apt/sources.list.d/python27-updates.list
        - keyid: FF3997E83CD969B409FB24BC5BB92C09DB82666C
        - keyserver: keyserver.ubuntu.com
        - require_in: python2.7-update

    python2.7-update:
      pkg.latest:
        - fromrepo: trusty
        - pkgs:
          - python2.7
          - python2.7-dev

    # needed to get the latest pip
    python-pip-bootstrap:
      cmd.run:
        - name: curl https://bootstrap.pypa.io/get-pip.py | python
        - reload_modules: true

    python-virtualenv:
      pip.installed:
        - name: 'virtualenv'
        - use_wheel: true

    app_venv:
      virtualenv.managed:
        - name: /venv

Layer Definition Using a Python Program
---------------------------------------

This layer is defined using a python program. It doesn't actually build
a new Docker image, but instead runs tests using a previously defined layer.
Here's the ``layer.yaml``:

.. code-block:: yaml

    help: Test Runner Layer
    description: >
      Flask Example App Test Runner, which runs
      unit and acceptance tests inside the Docker container.
    parent: app

Here's the python program that runs the tests — it must define a class that derives
from ``DockerBuildLayer``:

.. code-block:: python

    # -*- coding: utf-8 -*-

    from __future__ import unicode_literals, absolute_import, print_function

    import os

    from flyingcloud import DockerBuildLayer, CommandError


    class TestRunner(DockerBuildLayer):
        def do_build(self, namespace):
            namespace.logger.warning("TestRunner build does nothing")

        def do_run(self, namespace):
            test_type = namespace.test_type
            test_path = "/venv/lib/python2.7/site-packages/flask_example_app/tests"

            if test_type == "unit":
                test_dir = os.path.join(test_path, "unit")
            elif test_type == "acceptance":
                test_dir = os.path.join(test_path, "acceptance")
            else:
                raise ValueError("Unknown test_type: {}".format(test_type))

            if namespace.pull_layer and self.registry_config['pull_layer']:
                self.docker_pull(namespace, self.source_image_name)

            environment = {}
            if namespace.base_url:
                environment['BASE_URL'] = namespace.base_url

            namespace.logger.info(
                "Running tests: type=%s, environment=%r", test_type, environment)
            container_id = self.docker_create_container(
                namespace, None, self.source_image_name, environment=environment)
            self.docker_start(namespace, container_id)

            cmd = ["/venv/bin/py.test", "--tb=long", test_dir]
            result, full_output = self.docker_exec(
                namespace, container_id, cmd, raise_on_error=False)
            self.docker_stop(namespace, container_id)
            namespace.logger.info("Run tests: %r", result)
            namespace.logger.info("%s", full_output)
            exit_code = result['ExitCode']
            if exit_code != 0:
                raise CommandError("testrunner {}: exit code was non-zero: {}".format(
                    test_dir, exit_code))

        def do_kill(self, namespace):
            pass

        @classmethod
        def add_parser_options(cls, subparser):
            subparser.add_argument(
                '--test-type', '-T',
                default='unit',
                help="Test Type: 'unit' or 'acceptance'. Default: %(default)s")
            subparser.add_argument(
                '--base-url', '-B',
                help="Base URL for Acceptance tests")


