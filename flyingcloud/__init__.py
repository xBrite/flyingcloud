#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import datetime
import json
import tempfile

import StringIO
import docker
import logging
import os
import platform

import re
import sh
import time

STREAMING_CHUNK_SIZE = (1 << 20)


# TODO
# - do a better job of logging container-ids and image-ids
# - unit tests, using a mock docker-py

class EnvironmentVarError(Exception):
    pass


class NotSudoError(Exception):
    pass


class CommandError(Exception):
    pass


class ExecError(Exception):
    pass


class DockerBuildLayer(object):
    """Build a Docker image using SaltStack

    Can either build from a base image or from a Dockerfile.
    Uses Salt states to build each layer.
    Finished layers are pushed to the registry.
    """
    # Override these as necessary
    Registry = ''
    RegistryDockerVersion = None
    Organization = None
    AppName = None
    LayerName = None
    Description = None
    SquashLayer = False
    PushLayer = False
    LayerSuffix = None
    SourceImageName = None
    TargetImageName = None  # usually tagged with ":latest"
    SaltStateDir = None
    CommandName = None
    SaltExecTimeout = 40 * 60  # seconds, for long-running commands
    USERNAME_VAR = 'FLYINGCLOUD_DOCKER_REGISTRY_USERNAME'
    PASSWORD_VAR = 'FLYINGCLOUD_DOCKER_REGISTRY_PASSWORD'

    @classmethod
    def main(cls, defaults, *layer_classes, **kwargs):
        if os.geteuid() != 0 and platform.system() == "Linux":
            raise NotSudoError("You must be root (use sudo)")
        if cls.Registry:
            for v in [cls.USERNAME_VAR, cls.PASSWORD_VAR]:
                if v not in os.environ:
                    raise EnvironmentVarError("Environment variable {} not defined".format(v))
        namespace = cls.parse_args(defaults, *layer_classes, **kwargs)

        namespace.logger.info("Build starting...")
        namespace.func(namespace)
        namespace.logger.info("Build finished")

    def __init__(self):
        assert self.AppName
        assert self.LayerSuffix
        self.ContainerName = "{}_{}".format(self.AppName, self.LayerSuffix)
        if self.Registry and self.Organization:
            self.ImageName = "{}/{}/{}".format(self.Registry, self.Organization, self.ContainerName)
        else:
            self.ImageName = self.ContainerName
        # These require the command-line args to properly initialize
        self.layer_latest_name = self.layer_timestamp_name = self.layer_squashed_name = None
        self.source_image_name = self.SourceImageName

    def initialize_build(self, namespace, salt_dir):
        """Override if you need special handling"""
        pass

    def run_command(self, namespace, layer_strong_name, container_id):
        """Override if you need special handling"""
        pass

    def build(self, namespace):
        salt_dir = os.path.abspath(os.path.join(namespace.salt_dir, self.SaltStateDir))
        self.layer_latest_name = "{}:latest".format(self.ImageName)
        self.layer_timestamp_name = "{}:{}".format(self.ImageName, namespace.timestamp)
        self.layer_squashed_name = "{}-sq".format(self.layer_timestamp_name)

        self.initialize_build(namespace, salt_dir)

        self.docker_pull(namespace, self.source_image_name)

        container_name = self.salt_highstate(
            namespace, self.ContainerName,
            source_image_name=self.source_image_name,
            result_image_name=self.layer_timestamp_name,
            salt_dir=salt_dir)
        if namespace.squash_layer and self.SquashLayer:
            layer_strong_name = self.docker_squash(
                namespace,
                image_name=self.layer_timestamp_name,
                latest_image_name=self.layer_latest_name,
                squashed_image_name=self.layer_squashed_name)
            remove_layer = self.layer_timestamp_name
        else:
            layer_strong_name = self.layer_timestamp_name
            namespace.logger.info("Not squashing layer %s", layer_strong_name)
            remove_layer = None
            self.docker_tag(namespace, layer_strong_name, "latest")
        self.run_command(namespace, layer_strong_name, container_name)
        # TODO: make the following lines work consistently; on some Linux boxes, they don't work
        # if remove_layer:
        #     self.docker_remove_image(namespace, remove_layer)
        if namespace.push_layer and self.PushLayer:
            self.docker_push(
                namespace,
                layer_strong_name)
            self.docker_push(
                namespace,
                self.layer_latest_name)
        else:
            namespace.logger.info("Not pushing Docker layers.")
        return layer_strong_name

    def salt_highstate(
            self, namespace, container_name, source_image_name, result_image_name,
            salt_dir, timeout=SaltExecTimeout):
        """Use SaltStack to configure container"""
        namespace.logger.info(
            "Starting salt_highstate: source_image_name=%s, container_name=%s, salt_dir=%s",
            source_image_name, container_name, salt_dir)
        try:
            container_name = self.docker_create_container(
                namespace, container_name, source_image_name,
                volume_map={salt_dir: "/srv/salt"})

            self.docker_start(namespace, container_name)

            namespace.logger.info("About to start Salting")
            start_time = time.time()
            result, salt_output = self.docker_exec(
                namespace, container_name,
                ["salt-call", "--local", "state.highstate"],
                timeout)
            duration = round(time.time() - start_time)
            namespace.logger.info(
                "Finished Salting: duration=%d:%02d minutes", duration // 60, duration % 60)
            namespace.logger.debug("%r", salt_output)
            if self.salt_error(salt_output):
                raise ExecError("salt_highstate failed.")

            result = self.docker_commit(namespace, container_name, result_image_name)
            namespace.logger.info("Committed: %r", result)
        finally:
            self.docker_cleanup(namespace, container_name)
        return container_name

    @classmethod
    def salt_error(cls, salt_output):
        return re.search("\s*Failed:\s+[1-9]\d*\s*$", salt_output, re.MULTILINE) is not None

    @classmethod
    def build_dockerfile(cls, namespace, tag, dockerfile=None, fileobj=None):
        namespace.logger.info("About to build Dockerfile, tag=%s", tag)
        for line in namespace.docker.build(tag=tag, path=namespace.base_dir,
                                           dockerfile=dockerfile, fileobj=fileobj):
            namespace.logger.debug("%s", line)

    @classmethod
    def docker_create_container(
            cls, namespace, container_name, image_name,
            environment=None, detach=True, volume_map=None):
        namespace.logger.info("Creating container '%s' from image %s", container_name, image_name)
        container = namespace.docker.create_container(
            name=container_name,
            image=image_name,
            environment=environment,
            detach=detach,
            **cls.docker_volumes(namespace, volume_map)
        )
        container_id = container['Id']
        namespace.logger.info("Created container %s, result=%r", container_id[:12], container)
        return container_id

    @classmethod
    def docker_volumes(cls, namespace, volume_map):
        if not volume_map:
            return {}

        volumes, binds = [], []
        for local_path, remote_path in volume_map.items():
            volumes.append(remote_path)
            binds.append("{}:{}".format(os.path.abspath(local_path), remote_path))
        return dict(
            volumes=volumes,
            host_config=namespace.docker.create_host_config(binds=binds)
        )

    @classmethod
    def docker_start(cls, namespace, container_id):
        return namespace.docker.start(container_id)

    @classmethod
    def docker_exec(cls, namespace, container_id, cmd, timeout=None):
        exec_id = cls.docker_exec_create(namespace, container_id, cmd)
        return cls.docker_exec_start(namespace, exec_id, timeout)

    @classmethod
    def docker_exec_create(cls, namespace, container_id, cmd):
        namespace.logger.info("Running %r in container %s", cmd, container_id[:12])
        exec_create = namespace.docker.exec_create(container=container_id, cmd=cmd)
        return exec_create['Id']

    @classmethod
    def docker_exec_start(cls, namespace, exec_id, timeout=None):
        timeout = timeout or namespace.timeout or cls.SaltExecTimeout
        # Use a distinct client with a custom timeout
        # (synchronous execs can last much longer than 60 seconds)
        client = cls.docker_client(namespace, timeout=timeout)
        generator = client.exec_start(exec_id=exec_id, stream=True)
        full_output = cls.read_docker_output_stream(namespace, generator, "docker_exec")
        result = client.exec_inspect(exec_id=exec_id)
        exit_code = result['ExitCode']
        if exit_code != 0:
            raise ExecError("docker_exec exit code was non-zero: {} (result: {})".format(exit_code, result))
        return result, full_output

    @classmethod
    def read_docker_output_stream(cls, namespace, generator, logger_prefix):
        line = ''
        full_output = []
        for chunk in generator:
            line += chunk
            full_output.append(chunk)
            if line.endswith('\n'):
                namespace.logger.debug("%s: %s", logger_prefix, line.rstrip('\n'))
                line = ''
        return ''.join(full_output)

    @classmethod
    def docker_commit(cls, namespace, container_id, result_image_name):
        repo, tag = cls.image_name2repo_tag(result_image_name)
        return namespace.docker.commit(container=container_id, repository=repo, tag=tag)

    @classmethod
    def docker_squash(cls, namespace, image_name, latest_image_name, squashed_image_name):
        # TODO: handle no docker-squash binary; find path to docker-squash
        installation_prefix = os.environ.get('VIRTUAL_ENV', '/usr/local')
        docker_squash_cmd = sh.Command("{}/bin/docker-squash".format(installation_prefix))

        try:
            input_temp = tempfile.NamedTemporaryFile(suffix="-input-image.tar", delete=False)
            output_temp = tempfile.NamedTemporaryFile(suffix="-output-image.tar", delete=False)
            # docker save to tarfile
            image_raw = namespace.docker.get_image(image_name)
            for chunk in image_raw.stream(STREAMING_CHUNK_SIZE, decode_content=True):
                input_temp.write(chunk)
            input_temp.close()

            # docker-squash -i tar1 -o tar2
            # TODO: use subprocess.Popen and pipe input and output
            output_temp.close()
            namespace.logger.info("Squashing '%s' (%d bytes) to '%s'",
                                  input_temp.name, os.path.getsize(input_temp.name), output_temp.name)
            docker_squash_cmd("-i", input_temp.name, "-o", output_temp.name, "-t", latest_image_name,
                              "-from", "root")
            output_temp = open(output_temp.name, 'rb')

            # docker load tar2
            namespace.logger.info("Loading squashed image (%d bytes)", os.path.getsize(output_temp.name))
            namespace.docker.load_image(data=output_temp)
            output_temp.close()

            _, tag = cls.image_name2repo_tag(squashed_image_name)
            cls.docker_tag(namespace, latest_image_name, tag=tag)
        finally:
            os.unlink(input_temp.name)
            os.unlink(output_temp.name)

        return squashed_image_name

    @classmethod
    def docker_get_strong_name_of_latest_image(cls, namespace, image_name):
        images = namespace.docker.images()
        latest_image_name = image_name + ":latest"
        for image in images:
            repo_tags = set(image['RepoTags'])
            namespace.logger.info(repo_tags)
            if latest_image_name in repo_tags:
                repo_tags.remove(latest_image_name)
                result = repo_tags.pop()
                if result:
                    return result
                else:
                    return latest_image_name

    # TODO: cleanly remove all non-running containers
    @classmethod
    def docker_cleanup(cls, namespace, container_name):
        namespace.logger.info("docker_cleanup %s", container_name)
        cls.docker_stop(namespace, container_name)
        cls.docker_remove_container(namespace, container_name)

    @classmethod
    def docker_stop(cls, namespace, container_name):
        namespace.docker.stop(container_name)

    @classmethod
    def docker_remove_container(cls, namespace, container_name, force=True):
        namespace.docker.remove_container(container=container_name, force=force)

    @classmethod
    def docker_remove_image(cls, namespace, image_name, force=True):
        namespace.docker.remove_image(image=image_name, force=force)

    @classmethod
    def image_name2repo_tag(cls, image_name, tag=None):
        repo, image_tag = image_name.split(':')
        tag = tag or image_tag
        return repo, tag

    @classmethod
    def docker_tag(cls, namespace, image_name, tag=None, force=True):
        repo, tag = cls.image_name2repo_tag(image_name, tag)
        namespace.logger.info("Tagging image %s as repo=%s, tag=%s", image_name, repo, tag)
        namespace.docker.tag(image=image_name, repository=repo, tag=tag, force=force)

    @classmethod
    def docker_pull(cls, namespace, image_name):
        namespace.logger.info("docker_pull %s", image_name)
        repo, tag = cls.image_name2repo_tag(image_name)
        generator = namespace.docker.pull(repository=repo, tag=tag, stream=True)
        full_output = cls.read_docker_output_stream(namespace, generator, "docker_pull")

    @classmethod
    def docker_push(cls, namespace, image_name):
        namespace.logger.info("docker_push %s", image_name)
        repo, tag = cls.image_name2repo_tag(image_name)
        generator = namespace.docker.push(repository=repo, tag=tag, stream=True)
        full_output = cls.read_docker_output_stream(namespace, generator, "docker_push")
        # TODO: raise on error

    @classmethod
    def docker_login(cls, namespace):
        namespace.logger.info("Logging in to registry '%s' as user '%s'", cls.Registry, namespace.username)
        return namespace.docker.login(
            username=namespace.username, password=namespace.password, registry=cls.Registry)

    @classmethod
    def configure_logging(cls, namespace):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(namespace.logfile)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if namespace.debug else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        logger.addHandler(ch)
        logger.addHandler(fh)
        return logger

    @classmethod
    def add_additional_configuration(cls, namespace):
        """Override to add additional configuration to namespace"""
        pass

    @classmethod
    def parse_args(cls, defaults, *layer_classes, **kwargs):
        # TODO: require registry, organization, etc which have no good defaults
        parser = argparse.ArgumentParser(
            description=kwargs.pop('description', "Build a Docker image using SaltStack"))

        defaults = defaults or {}
        # TODO: review setting up base_dir, etc when the invoking script is in a different directory
        defaults.setdefault('base_dir', os.path.abspath(os.path.dirname(__file__)))
        defaults.setdefault('salt_dir', os.path.join(defaults['base_dir'], "salt"))
        defaults.setdefault('logfile', os.path.join(defaults['base_dir'], "build_docker.log"))
        defaults.setdefault('timestamp_format', '%Y-%m-%dT%H%M-%SZ')
        defaults.setdefault(
            'timestamp', datetime.datetime.utcnow().strftime(defaults['timestamp_format']))
        defaults.setdefault('squash_layer', True)
        defaults.setdefault('push_layer', True)

        parser.set_defaults(
            **defaults
        )
        parser.add_argument(
            '--timeout', '-t', type=int, default=1 * 60,
            help="Docker client timeout in seconds. Default: %(default)s")
        parser.add_argument(
            '--no-squash', '-S', dest='squash_layer', action='store_false',
            help="Do not squash Docker layers")
        parser.add_argument(
            '--no-push', '-P', dest='push_layer', action='store_false',
            help="Do not push Docker layers")
        parser.add_argument(
            '--debug', '-D', dest='debug', action='store_true',
            help="Set terminal logging level to debug")
        subparsers = parser.add_subparsers(help="sub-command")

        for layer_cls in layer_classes:
            subparser = subparsers.add_parser(
                layer_cls.CommandName, help=layer_cls.Description)
            subparser.set_defaults(
                func=layer_cls().build)
            layer_cls.add_parser_options(subparser)

        namespace = parser.parse_args()

        namespace.logger = cls.configure_logging(namespace)
        namespace.username = os.environ[cls.USERNAME_VAR]
        namespace.password = os.environ[cls.PASSWORD_VAR]
        namespace.docker = cls.docker_client(namespace, timeout=namespace.timeout)
        if cls.Registry:
            cls.docker_login(namespace)

        cls.add_additional_configuration(namespace)

        return namespace

    @classmethod
    def add_parser_options(cls, subparser):
        pass

    @classmethod
    def docker_client(cls, namespace, *args, **kwargs):
        namespace.logger.info("Platform is '{}'.".format(platform.system()))
        if cls.RegistryDockerVersion:
            kwargs.setdefault('version', cls.RegistryDockerVersion)
        if platform.system() == "Darwin":
            kwargs = cls.get_docker_machine_client(namespace, **kwargs)
        return docker.Client(*args, **kwargs)

    @classmethod
    def get_docker_machine_client(cls, namespace, **kwargs):
        # TODO: better error handling
        docker_machine = sh.Command("docker-machine")
        output = StringIO.StringIO()
        docker_machine("inspect", "default", _out=output)
        docker_machine_json = output.getvalue()
        namespace.logger.debug("docker-machine json: {}".format(docker_machine_json))
        namespace.logger.debug("docker-machine json type: {}".format(type(docker_machine_json)))
        docker_machine_json = json.loads(docker_machine_json)
        docker_machine_tls = docker_machine_json['HostOptions']['AuthOptions']
        docker_machine_ip = docker_machine_json['Driver']['IPAddress']
        base_url = 'https://' + docker_machine_ip + ':2376'
        kwargs['base_url'] = base_url
        kwargs['tls'] = docker.tls.TLSConfig(
            client_cert=(docker_machine_tls['ClientCertPath'],
                         docker_machine_tls['ClientKeyPath']),
            ca_cert=docker_machine_tls['CaCertPath'],
            assert_hostname=False,
            verify=True)
        namespace.logger.info("Using '{}' as Docker base_url".format(base_url))
        return kwargs

