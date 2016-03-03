# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os

from flyingcloud import BuildLayerBase, CommandError


class TestRunner(BuildLayerBase):
    def build(self, namespace):
        test_type = namespace.test_type
        image_name = self.SourceImageName
        if self.PullLayer:
            self.docker_pull(namespace, image_name)

        namespace.logger.info("Running tests: type=%s", test_type)
        test_root = os.path.abspath(os.path.dirname(__file__))
        share_dir = os.path.join(test_root, 'share')
        container_id = self.docker_create_container(
            namespace, None, image_name,
            volume_map={share_dir: '/mnt/share'})
        self.docker_start(namespace, container_id)

        nosetest_filename = "nosetests-{}.xml".format(test_type)
        fab_task_args_format = "bamboo=yes,xunit_file=/mnt/share/{}"

        if test_type == "unit":
            fab_target = "run_tests"
            fab_task_args = fab_task_args_format.format(
                nosetest_filename)
        elif test_type == "acceptance":
            fab_target = "run_acceptance_tests"
        else:
            raise ValueError("Unknown test_type: {}".format(test_type))

        cmd = [
            "/venv/bin/fab",
            "-f",
            "/application/ocr/fabfile.py",
            "{}:{}".format(fab_target, fab_task_args)]
        result = self.docker_exec(
            namespace, container_id, cmd, raise_on_error=False)
        namespace.logger.debug("Run tests: %r", result)
        self.docker_stop(namespace, container_id)
        result_filename = os.path.join(share_dir, nosetest_filename)
        namespace.logger.info("Results at %s", result_filename)

        root = objectify.parse(result_filename).getroot()
        failures = int(root.attrib['failures'])
        errors = int(root.attrib['errors'])
        tests = int(root.attrib['tests'])

        if failures > 0 or errors > 0:
            errmsg = "CookBriteBuildLecternWorkerLayer: {}: " \
                     "failures={}, errors={}, tests={}".format(
                result_filename, failures, errors, tests)
            namespace.logger.info(errmsg)
            with open(result_filename) as fp:
                namespace.logger.info("%s", fp.read())
            raise CommandError(errmsg)
        else:
            namespace.logger.info("%d tests passed", tests)

    @classmethod
    def add_parser_options(cls, subparser):
        subparser.add_argument(
            '--test-type', '-T',
            default='unit',
            help="Test Type: 'unit' or 'acceptance'. Default: %(default)s")
