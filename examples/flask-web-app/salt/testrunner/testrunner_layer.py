# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os
import time

from flyingcloud import DockerBuildLayer, CommandError


class TestRunner(DockerBuildLayer):
    def do_build(self, namespace):
        namespace.logger.warning("TestRunner build does nothing")

    def do_run(self, namespace):
        test_type = namespace.test_type
        test_path = "/venv/lib/python2.7/site-packages/flask_example_app/tests"
        sleep_interval = 2.0
        environment = self.make_environment_dict(namespace)

        if test_type == "unit":
            test_dir = os.path.join(test_path, "unit")
        elif test_type == "acceptance":
            test_dir = os.path.join(test_path, "acceptance")
        else:
            raise ValueError("Unknown test_type: {}".format(test_type))

        if namespace.pull_layer and self.registry_config['pull_layer']:
            self.docker_pull(namespace, self.source_image_name)

        if namespace.base_url:
            environment['BASE_URL'] = namespace.base_url

        namespace.logger.info(
            "Running tests: type=%s, environment=%r", test_type, environment)
        container_id = self.docker_create_container(
            namespace,
            self.container_name,
            self.source_image_name,
            environment=environment)
        self.docker_start(namespace, container_id)
        namespace.logger.info("Sleeping for %.1f seconds", sleep_interval)
        time.sleep(sleep_interval)

        try:
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
        finally:
            self.docker_stop(namespace, container_id)
            self.docker_remove_container(namespace, self.container_name)

    def do_kill(self, namespace):
        pass

    def make_environment_dict(self, namespace):
        environment = {
            'VIRTUAL_ENV': '/venv'
        }
        if namespace.env_vars:
            environment.update(namespace.env_vars)
        return environment

    @classmethod
    def add_parser_options(cls, subparser):
        subparser.add_argument(
            '--test-type', '-T',
            default='unit',
            help="Test Type: 'unit' or 'acceptance'. Default: %(default)s")
        subparser.add_argument(
            '--base-url', '-B',
            help="Base URL for Acceptance tests")
