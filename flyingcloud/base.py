#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import datetime
import glob
from io import BytesIO
import json
import tempfile

import StringIO
import docker
import logging
import os
import platform
import requests

import re
import sh
import time

from .utils import disk_usage, abspath

STREAMING_CHUNK_SIZE = (1 << 20)


# TODO
# - do a better job of logging container-ids and image-ids
# - unit tests, using a mock docker-py

class FlyingCloudError(Exception):
    """Base error"""


class EnvironmentVarError(FlyingCloudError):
    """Missing environment variable"""


class NotSudoError(FlyingCloudError):
    """Not running as root"""


class CommandError(FlyingCloudError):
    """Command failure"""


class ExecError(FlyingCloudError):
    """Failure to run a command in Docker container"""


class DockerResultError(FlyingCloudError):
    """Error in result from Docker Daemon"""


class _DockerBuildLayer(object):
    """Build a Docker image using SaltStack

    Can either build from a base image or from a Dockerfile.
    Uses Salt states to build each layer.
    Finished layers are pushed to the registry.
    """
    # Override these as necessary
    Registry = ''
    RegistryDockerVersion = None
    LoginRequired = True
    Organization = None
    AppName = None
    LayerName = None
    Description = None
    PullLayer = True
    PushLayer = False
    SquashLayer = False
    LayerSuffix = None
    SourceImageName = None
    TargetImageName = None  # usually tagged with ":latest"
    SaltStateDir = None
    CommandName = None
    SaltExecTimeout = 45 * 60  # seconds, for long-running commands
    DefaultTimeout = 5 * 60  # need longer than default timeout for most commands
    ExposedPorts = None
    SourceImageBaseName = None
    USERNAME_VAR = 'FLYINGCLOUD_DOCKER_REGISTRY_USERNAME'
    PASSWORD_VAR = 'FLYINGCLOUD_DOCKER_REGISTRY_PASSWORD'

    def main(self, defaults, *layer_classes, **kwargs):
        self.check_root()
        self.check_environment_variables()
        namespace = self.parse_args(defaults, *layer_classes, **kwargs)
        self.run_build(namespace)

    @classmethod
    def check_root(cls):
        if os.geteuid() != 0 and platform.system() == "Linux":
            raise NotSudoError("You must be root (use sudo)")

    def check_environment_variables(self):
        if self.Registry:
            for v in [self.USERNAME_VAR, self.PASSWORD_VAR]:
                if v not in os.environ and self.LoginRequired:
                    raise EnvironmentVarError("Environment variable {} not defined".format(v))

    def run_build(self, namespace):
        namespace.logger.info("Build starting...")
        self.log_disk_usage(namespace)
        self.docker_info(namespace)
        if namespace.layer_inst.should_build(namespace):
            namespace.func(namespace)
        namespace.logger.info("Build finished")

    def __init__(self, appname=None, command_name=None,
                 layer_suffix=None, salt_state_dir=None):
        self.AppName = appname or self.AppName
        self.CommandName = command_name or self.CommandName
        self.SaltStateDir = salt_state_dir or self.SaltStateDir or self.CommandName
        self.LayerSuffix = layer_suffix or self.LayerSuffix or self.CommandName
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

    def should_build(self, namespace):
        return True

    def initialize_build(self, namespace, salt_dir):
        """Override if you need special handling"""
        pass

    def run_command(self, namespace, layer_strong_name, container_id):
        """Override if you need special handling"""
        pass

    def set_layer_defaults(self):
        self.TargetImagePrefixName = "{}/{}/{}_{}".format(
            self.Registry, self.Organization, self.AppName, self.CommandName)
        self.source_image_name = self.SourceImageName = "{}/{}/{}".format(
            self.Registry, self.Organization, self.SourceImageBaseName)
        self.TargetImageName = self.TargetImagePrefixName + ":latest"

    def build(self, namespace):
        salt_dir = os.path.abspath(os.path.join(namespace.salt_dir, self.SaltStateDir))

        if not os.path.exists(salt_dir):
            message = "Configuration directory %s does not exist, failing!" % salt_dir
            namespace.logger.error(message)
            raise CommandError(message)

        self.layer_latest_name = "{}:latest".format(self.ImageName)
        self.layer_timestamp_name = "{}:{}".format(self.ImageName, namespace.timestamp)
        self.layer_squashed_name = "{}-sq".format(self.layer_timestamp_name)

        self.initialize_build(namespace, salt_dir)
        dockerfile = self.get_dockerfile(salt_dir)
        if dockerfile:
            self.auto_build_dockerfile(namespace, dockerfile)
        else:
            self.expose_ports(namespace)

        if self.PullLayer:
            self.docker_pull(namespace, self.source_image_name)

        container_name = self.salt_highstate(
            namespace, self.ContainerName,
            source_image_name=self.source_image_name or self.ImageName,
            result_image_name=self.layer_timestamp_name,
            salt_dir=salt_dir)
        layer_strong_name = None
        if namespace.squash_layer and self.SquashLayer:
            layer_strong_name = self.docker_squash(
                namespace,
                image_name=self.layer_timestamp_name,
                latest_image_name=self.layer_latest_name,
                squashed_image_name=self.layer_squashed_name)
            remove_layer = self.layer_timestamp_name
        if layer_strong_name is None:
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

    def get_dockerfile(self, salt_dir):
        df = os.path.join(salt_dir, "Dockerfile")
        return df if os.path.exists(df) else None

    def auto_build_dockerfile(self, namespace, dockerfile):
        namespace.logger.info("Building %s", dockerfile)
        self.source_image_name = self.build_dockerfile(namespace, self.layer_timestamp_name, dockerfile=dockerfile)

    def expose_ports(self, namespace):
        if self.ExposedPorts:
            port_list = " ".join(str(p) for p in self.ExposedPorts)
            Dockerfile = """
                FROM {}
                EXPOSE {}
            """.format(self.SourceImageName, port_list)
            namespace.logger.info("Exposing ports: %s", port_list)
            fileobj = BytesIO(Dockerfile.encode('utf-8'))
            self.build_dockerfile(namespace, self.layer_timestamp_name, fileobj=fileobj)

    def salt_states_exist(self, salt_dir):
        files = glob.glob(os.path.join(salt_dir, '*.sls'))
        return len(files)

    def salt_highstate(
            self, namespace, container_name, source_image_name, result_image_name,
            salt_dir, timeout=SaltExecTimeout):
        """Use SaltStack to configure container"""
        if not self.salt_states_exist(salt_dir):
            namespace.logger.info("No salt states found, not salting.")
            return None
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
            if self.salt_error(salt_output):
                raise ExecError("salt_highstate failed.")

            result = self.docker_commit(namespace, container_name, result_image_name)
            namespace.logger.info("Committed: %r", result)
        except:
            namespace.logger.exception("Salting failed")
            raise
        finally:
            self.docker_cleanup(namespace, container_name)
        return container_name

    def salt_error(self, salt_output):
        return re.search("\s*Failed:\s+[1-9]\d*\s*$", salt_output, re.MULTILINE) is not None

    def build_dockerfile(self, namespace, tag, dockerfile=None, fileobj=None):
        namespace.logger.info("About to build Dockerfile, tag=%s", tag)
        if dockerfile:
            dockerfile = os.path.relpath(dockerfile, namespace.base_dir)
        for line in namespace.docker.build(tag=tag, path=namespace.base_dir,
                                           dockerfile=dockerfile, fileobj=fileobj):
            line = line.rstrip('\r\n')
            namespace.logger.debug("%s", line)
        # Grrr! Why doesn't docker-py handle this for us?
        match = re.search(r'Successfully built ([0-9a-f]+)', line)
        image_id = match and match.group(1)
        namespace.logger.info("Built tag=%s, image_id=%s", tag, image_id)
        return image_id

    def docker_create_container(
            self, namespace, container_name, image_name,
            environment=None, detach=True, volume_map=None):
        namespace.logger.info("Creating container '%s' from image %s", container_name, image_name)
        namespace.logger.debug(
            "Tags for image '%s': %s",
            image_name, self.docker_tags_for_image(namespace, image_name))
        container = namespace.docker.create_container(
            image=image_name,
            name=container_name,
            environment=environment,
            detach=detach,
            **self.docker_volumes(namespace, volume_map))
        container_id = container['Id']
        namespace.logger.info("Created container %s, result=%r", container_id[:12], container)
        return container_id

    def log_disk_usage(self, namespace, *extra_paths):
        for path in (
                '/',
                abspath('~/.docker'),
                '/var/lib/docker',
                tempfile.gettempdir()) + extra_paths:
            if os.path.exists(path):
                namespace.logger.info("Disk Usage '%s': %r", path, disk_usage(path))

    def docker_tags_for_image(self, namespace, image_name):
        parts = image_name.split('/')
        if len(parts) == 3 and namespace.username and namespace.password:
            url = "https://{0}/v1/repositories/{1}/{2}/tags".format(
                parts[0], parts[1], parts[2].split(':')[0])
            r = requests.get(url, auth=(namespace.username, namespace.password))
            return r.json()

    def docker_volumes(self, namespace, volume_map):
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

    def docker_start(self, namespace, container_id):
        return namespace.docker.start(container_id)

    def docker_exec(self, namespace, container_id, cmd, timeout=None, raise_on_error=True):
        exec_id = self.docker_exec_create(namespace, container_id, cmd)
        return self.docker_exec_start(namespace, exec_id, timeout, raise_on_error)

    def docker_exec_create(self, namespace, container_id, cmd):
        namespace.logger.info("Running %r in container %s", cmd, container_id[:12])
        exec_create = namespace.docker.exec_create(container=container_id, cmd=cmd)
        return exec_create['Id']

    def docker_exec_start(self, namespace, exec_id, timeout=None, raise_on_error=True):
        timeout = timeout or namespace.timeout or self.SaltExecTimeout
        # Use a distinct client with a custom timeout
        # (synchronous execs can last much longer than 60 seconds)
        client = self.docker_client(namespace, timeout=timeout)
        generator = client.exec_start(exec_id=exec_id, stream=True)
        full_output = self.read_docker_output_stream(namespace, generator, "docker_exec")
        result = client.exec_inspect(exec_id=exec_id)
        exit_code = result['ExitCode']
        if exit_code != 0 and raise_on_error:
            raise ExecError("docker_exec exit code was non-zero: {} (result: {})".format(exit_code, result))
        return result, full_output

    def read_docker_output_stream(self, namespace, generator, logger_prefix):
        full_output = []
        for chunk in generator:
            full_output.append(chunk)
            try:
                data = json.loads(chunk)
            except ValueError:
                data = chunk.rstrip('\r\n')
            namespace.logger.debug("%s: %s", logger_prefix, data)
            if isinstance(data, dict) and 'error' in data:
                raise DockerResultError("Error: {!r}".format(data))
        return '\n'.join(full_output)

    def docker_commit(self, namespace, container_id, result_image_name):
        repo, tag = self.image_name2repo_tag(result_image_name)
        return namespace.docker.commit(container=container_id, repository=repo, tag=tag)

    def find_binary(self, namespace, filename, search_paths=None):
        if search_paths is None:
            search_paths = [os.environ.get('VIRTUAL_ENV'), '/usr/local']
            search_paths = [os.path.join(p, "bin") for p in search_paths if p]
        for path in search_paths:
            filepath = os.path.join(path, filename)
            if os.path.exists(filepath):
                return filepath
        namespace.logger.info("Can't find '%s' in %s", filename, search_paths)
        return None

    def docker_squash(self, namespace, image_name, latest_image_name, squashed_image_name):
        docker_squash_path = self.find_binary(namespace, 'docker-squash')
        if docker_squash_path is None:
            namespace.logger.info("Not squashing")
            return None
        else:
            namespace.logger.info("Using %s", docker_squash_path)
        docker_squash_cmd = sh.Command(docker_squash_path)

        self.log_disk_usage(namespace)
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

            _, tag = self.image_name2repo_tag(squashed_image_name)
            self.docker_tag(namespace, latest_image_name, tag=tag)
        finally:
            os.unlink(input_temp.name)
            os.unlink(output_temp.name)

        return squashed_image_name

    def docker_get_strong_name_of_latest_image(self, namespace, image_name):
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
    def docker_cleanup(self, namespace, container_name):
        namespace.logger.info("docker_cleanup %s", container_name)
        self.docker_stop(namespace, container_name)
        self.docker_remove_container(namespace, container_name)

    def docker_stop(self, namespace, container_name):
        namespace.docker.stop(container_name)

    def docker_remove_container(self, namespace, container_name, force=True):
        namespace.docker.remove_container(container=container_name, force=force)

    def docker_remove_image(self, namespace, image_name, force=True):
        namespace.docker.remove_image(image=image_name, force=force)

    def image_name2repo_tag(self, image_name, tag=None):
        repo, image_tag = image_name.split(':')
        tag = tag or image_tag
        return repo, tag

    def docker_tag(self, namespace, image_name, tag=None, force=True):
        repo, tag = self.image_name2repo_tag(image_name, tag)
        namespace.logger.info("Tagging image %s as repo=%s, tag=%s", image_name, repo, tag)
        namespace.docker.tag(image=image_name, repository=repo, tag=tag, force=force)

    def docker_pull(self, namespace, image_name):
        return self._docker_push_pull(namespace, image_name, "pull")

    def docker_push(self, namespace, image_name):
        return self._docker_push_pull(namespace, image_name, "push")

    def _docker_push_pull(self, namespace, image_name, verb):
        give_up_message = "Couldn't {} {}. Giving up after {} attempts.".format(
            verb, image_name, namespace.retries)
        for attempt in range(1, namespace.retries + 1):
            try:
                namespace.logger.info("docker_%s %s, attempt %d/%d",
                                      verb, image_name, attempt, namespace.retries)
                repo, tag = self.image_name2repo_tag(image_name)
                method = getattr(namespace.docker, verb)
                generator = method(repository=repo, tag=tag, stream=True)
                return self.read_docker_output_stream(
                    namespace, generator, "docker_{}".format(verb))
            except DockerResultError:
                if attempt == namespace.retries:
                    namespace.logger.info("%s", give_up_message)
                    raise
        else:
            raise DockerResultError(give_up_message)

    def docker_login(self, namespace):
        assert not self.LoginRequired or namespace.username, "No username"
        assert not self.LoginRequired or namespace.password, "No password"
        if namespace.username and namespace.password:
            namespace.logger.info("Logging in to registry '%s' as user '%s'", self.Registry, namespace.username)
            return namespace.docker.login(
                username=namespace.username, password=namespace.password, registry=self.Registry)

    def docker_info(self, namespace):
        info = namespace.docker.info()
        namespace.logger.info("Docker Info: %r", info)
        return info

    def configure_logging(self, namespace):
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

    def add_additional_configuration(self, namespace):
        """Override to add additional configuration to namespace"""
        pass

    def parse_args(self, defaults, *layer_classes, **kwargs):
        # TODO: require registry, organization, etc which have no good defaults
        parser = argparse.ArgumentParser(
            description=kwargs.pop('description', "Build a Docker image using SaltStack"))

        defaults = defaults or {}
        # TODO: review setting up base_dir, etc when the invoking script is in a different directory
        defaults.setdefault('base_dir', os.path.abspath(os.path.dirname(__file__)))
        defaults.setdefault('salt_dir', os.path.join(defaults['base_dir'], "salt"))
        defaults.setdefault('logfile', os.path.join(defaults['base_dir'], "build_docker.log"))
        defaults.setdefault('timestamp_format', '%Y-%m-%dt%H%M%Sz')
        defaults.setdefault(
            'timestamp', datetime.datetime.utcnow().strftime(defaults['timestamp_format']))
        defaults.setdefault('squash_layer', True)
        defaults.setdefault('push_layer', True)
        defaults.setdefault('retries', 3)
        defaults.setdefault('layer_inst', self)

        parser.set_defaults(**defaults)

        parser.add_argument(
            '--timeout', '-t', type=int, default=self.DefaultTimeout,
            help="Docker client timeout in seconds. Default: %(default)s")
        parser.add_argument(
            '--no-squash', '-S', dest='squash_layer', action='store_false',
            help="Do not squash Docker layers")
        parser.add_argument(
            '--no-push', '-P', dest='push_layer', action='store_false',
            help="Do not push Docker layers")
        parser.add_argument(
            '--retries', '-R', dest='retries', type=int,
            help="How often to retry remote Docker operations, such as push/pull. "
                 "Default: %(default)s")
        parser.add_argument(
            '--debug', '-D', dest='debug', action='store_true',
            help="Set terminal logging level to debug")
        subparsers = parser.add_subparsers(help="sub-command")

        for layer_class_or_inst in layer_classes:
            if type(layer_class_or_inst).__name__ == 'classobj':
                layer_inst = layer_class_or_inst()
            else:
                layer_inst = layer_class_or_inst
            func = layer_inst.build
            subparser = subparsers.add_parser(
                layer_inst.CommandName, help=layer_inst.Description)
            subparser.set_defaults(
                layer_inst=layer_inst,
                func=func)
            layer_inst.add_parser_options(subparser)

        namespace = parser.parse_args()

        namespace.logger = self.configure_logging(namespace)
        namespace.username = os.environ.get(self.USERNAME_VAR)
        namespace.password = os.environ.get(self.PASSWORD_VAR)
        namespace.docker = self.docker_client(namespace, timeout=namespace.timeout)
        if self.Registry:
            self.docker_login(namespace)

        self.add_additional_configuration(namespace)

        return namespace

    @classmethod
    def add_parser_options(cls, subparser):
        pass

    def docker_client(self, namespace, *args, **kwargs):
        namespace.logger.info("Platform is '{}'.".format(platform.system()))
        kwargs.setdefault('timeout', self.DefaultTimeout)
        if self.RegistryDockerVersion:
            kwargs.setdefault('version', self.RegistryDockerVersion)
        if platform.system() == "Darwin":
            kwargs = self.get_docker_machine_client(namespace, **kwargs)
        namespace.logger.debug("Constructing docker client object with %s", kwargs)
        return docker.Client(*args, **kwargs)

    def get_docker_machine_client(self, namespace, **kwargs):
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
        namespace.logger.info("Docker-Machine: using {}".format(kwargs))
        return kwargs


class BuildLayerBase(_DockerBuildLayer):
    """Class to derive from"""
