# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os

from flyingcloud import DockerBuildLayer, CommandError


class TestRunner(DockerBuildLayer):
    def build(self, namespace):
        test_type = namespace.test_type
        test_path = "/venv/lib/python2.7/site-packages/flask_example_app/tests"

        if test_type == "unit":
            test_dir = os.path.join(test_path, "unit")
        elif test_type == "acceptance":
            test_dir = os.path.join(test_path, "acceptance")
        else:
            raise ValueError("Unknown test_type: {}".format(test_type))

        if namespace.pull_layer and self.registry_config['PullLayer']:
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

    @classmethod
    def add_parser_options(cls, subparser):
        subparser.add_argument(
            '--test-type', '-T',
            default='unit',
            help="Test Type: 'unit' or 'acceptance'. Default: %(default)s")
        subparser.add_argument(
            '--base-url', '-B',
            help="Base URL for Acceptance tests")
