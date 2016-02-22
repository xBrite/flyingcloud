#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import argparse
import datetime
import errno
import json
import logging
import os
import time
import boto, boto3
import jmespath
import sh
import sys

from boto.ec2 import autoscale
from boto.ec2 import elb
from boto.route53 import connect_to_region
from jinja2 import Environment, FileSystemLoader

import route53
from elb import AwsIngressMixin

# TODO
# - make delete really work
#   - delete loadbalancers
#   - get network interfaces, detach them
#   - delete vpc
#   - delete cloudformation stack
#   - delete cluster A record
# - remove cookbrite-specific details
#   - create metakube.yaml config file
# - json output
# - remove sleeps
#   - poll kube-aws for done status
#   - poll vagrant for done status
#   - poll kubernetes for done status
# - local registry
#   - optionally use instead of remote
#   - spin up
#   - push images to it
# - refactor elb


INI_FILES = {'local': 'local.ini',
             'dev': 'development.ini',
             'stg': 'staging.ini',
             'prod': 'production.ini'}


class EnvironmentVarError(Exception):
    pass


class MetaKube(object):
    RequiredEnvironmentVariables = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']

    @classmethod
    def main(cls, defaults, *provider_classes, **kwargs):
        for v in cls.RequiredEnvironmentVariables:
            if v not in os.environ:
                raise EnvironmentVarError("Environment variable '{}' not defined".format(v))
        namespace = cls.parse_args(defaults, *provider_classes, **kwargs)

        namespace.logger.info("MetaKube starting...")
        namespace.logger.info("Cluster name is '{}'".format(namespace.cluster_name))

        providers = {c.ProviderName: c for c in provider_classes}
        provider_name = namespace.provider
        provider = providers[provider_name](namespace)
        method = getattr(provider, namespace.command)
        if method:
            method()
        else:
            namespace.logger.error("Command {}.{} not found.".format(provider_name, namespace.command))

        namespace.logger.info("MetaKube finished.")

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
    def add_parser_options(cls, subparser):
        pass

    @classmethod
    def parse_args(cls, defaults, *layer_classes, **kwargs):
        parser = argparse.ArgumentParser(
            description=kwargs.pop('description', "Kubernetes cluster operations"))

        defaults = defaults or {}
        defaults.setdefault('base_dir', os.path.abspath(os.path.dirname(__file__)))
        defaults.setdefault('logfile', os.path.join(defaults['base_dir'], "metakube.log"))
        defaults.setdefault('timestamp_format', '%Y-%m-%dT%H%M-%SZ')
        defaults.setdefault(
            'timestamp', datetime.datetime.utcnow().strftime(defaults['timestamp_format']))
        defaults.setdefault('aws_kube_wait_time', 180)
        defaults.setdefault('aws_cluster_wait_time', 120)
        defaults.setdefault('vagrant_kube_wait_time', 120)
        defaults.setdefault('vagrant_cluster_wait_time', 60)

        parser.set_defaults(
            **defaults
        )
        parser.add_argument(
            '--config-dir', '-C',
            default='.',
            help="Configuration directory (defaults to current working directory)")
        parser.add_argument(
            '--aws', '-A', dest='provider', action='store_const', const='aws',
            help="Set target environment to AWS")
        parser.add_argument(
            '--vagrant', '-V', dest='provider', action='store_const', const='vagrant',
            help="Set target environment to local Vagrant")
        parser.add_argument(
            '--release-level', '-L',
            default='dev',
            help="Release-level, one of (dev, stg, prod, test, or something else)")
        parser.add_argument(
            '--nodes', '-N', dest='node_count', type=int, default=None,
            help="Specify number of nodes to spin up (AWS only; default: 3)")
        parser.add_argument(
            '--role', '-R',
            default='kube',
            help="Cluster base name (combined with release-level to produce the cluster name)")
        parser.add_argument(
            '--debug', '-D', dest='debug', action='store_true',
            help="Set terminal logging level to debug")
        parser.add_argument(
            'command',
            choices=['create', 'destroy', 'scale'],
            help="Operation to perform"
        )

        namespace = parser.parse_args()
        namespace.logger = cls.configure_logging(namespace)
        cls.add_additional_configuration(namespace)
        namespace.cluster_name = '{}-{}'.format(namespace.release_level, namespace.role)

        if not namespace.provider:
            namespace.logger.error("No provider specified - exiting.")
            print("You must specify a provider (--aws or --vagrant)")
            sys.exit(1)

        if namespace.config_dir:
            namespace.config_dir = os.path.abspath(namespace.config_dir)

        if namespace.provider == 'vagrant' and namespace.node_count > 1:
            parser.error("Specifying a node count for Vagrant is not supported.")
        elif namespace.provider == 'aws' and namespace.node_count is None:
            namespace.node_count = 3

        return namespace


class MetaKubeCloudProvider(object):
    ProviderName = None
    TemplateExtension = '.yt'
    ConfigFileExtension = '.yaml'

    def __init__(self, namespace):
        self.namespace = namespace
        self.logger = namespace.logger
        self._kubectl = sh.Command('kubectl')

        self.cluster_dir = os.path.abspath(os.path.join('clusters', namespace.cluster_name))
        self.cluster_provider_dir = os.path.join(self.cluster_dir, 'provider')
        self.cluster_services_dir = os.path.join(self.cluster_dir, 'services')

        os.environ['RELEASE_LEVEL'] = namespace.release_level

        self.template_variables = {
            'cluster_name': namespace.cluster_name,
            'cookbrite_ini_config_file': INI_FILES[os.environ['RELEASE_LEVEL']],
            'cookbrite_release_level': os.environ['RELEASE_LEVEL'],
            'cookbrite_flower_oauth2_secret': os.environ['COOKBRITE_FLOWER_OAUTH2_SECRET'],
            'cookbrite_production_aws_access_key_id': os.environ['COOKBRITE_PRODUCTION_AWS_ACCESS_KEY_ID'],
            'cookbrite_production_aws_secret_access_key': os.environ['COOKBRITE_PRODUCTION_AWS_SECRET_ACCESS_KEY'],
            'cookbrite_broker_url': os.environ['COOKBRITE_BROKER_URL']
        }

    @classmethod
    def search_json(cls, expression, json_string):
        data = json.loads(json_string)
        result = jmespath.search(expression, data)
        if result:
            if len(result) == 1:
                return result[0]
            else:
                return result

    @classmethod
    def mkdir_p(cls, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    @classmethod
    def get_file_paths_in_dir(cls, dir, extension, abspath=False):
        dirpath = os.path.abspath(dir)
        filenames = os.listdir(dirpath)
        filenames = [filename for filename in filenames if filename.endswith(extension)]
        if abspath:
            filenames = [os.path.join(os.path.abspath(dir), filename) for filename in filenames]
        return filenames

    @classmethod
    def get_template_files_in_dir(cls, dir, abspath=True):
        return cls.get_file_paths_in_dir(dir, cls.TemplateExtension, abspath=abspath)

    @classmethod
    def get_config_files_in_dir(cls, dir, abspath=True):
        return cls.get_file_paths_in_dir(dir, cls.ConfigFileExtension, abspath=abspath)

    @classmethod
    def render_template(cls, template_dir, template_file, template_variables):
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        result = template.render(**template_variables)
        return result

    def execute_command_and_log_output(self, command, parameters):
        output_lines = []
        command_name = command.__name__
        if command_name.find('/') > -1:
            command_name = command_name.split('/')[-1]
        for line in command(*parameters, _iter=True):
            self.logger.debug('[] %s'.format(command_name), line.strip())
            output_lines.append(line)
        return output_lines

    def render_templates(self, source_dir, destination_dir, template_variables):
        self.logger.info("source_dir: %s", source_dir)
        template_filenames = self.get_template_files_in_dir(source_dir, abspath=False)
        rendered_file_paths = []
        for template_filename in template_filenames:
            rendered_file_contents = self.render_template(source_dir, template_filename, template_variables)
            rendered_file_path = os.path.abspath(os.path.join(destination_dir, template_filename)).replace(
                self.TemplateExtension, self.ConfigFileExtension)
            self.mkdir_p(os.path.dirname(rendered_file_path))
            self.logger.debug("Writing config file '{}'".format(rendered_file_path))
            with open(rendered_file_path, 'w') as config_file:
                config_file.write(rendered_file_contents)
            rendered_file_paths.append(rendered_file_path)
        return rendered_file_paths

    def render_provider_config(self):
        provider_templates_dir = os.path.join(self.namespace.config_dir, self.ProviderName)
        self.render_templates(provider_templates_dir, self.cluster_provider_dir, self.template_variables)

    def render_services_config(self):
        services_templates_dir = os.path.join(self.namespace.config_dir, 'services')
        self.render_templates(services_templates_dir, self.cluster_services_dir, self.template_variables)

    def kubectl(self, *args):
        kubeconfig_path = os.path.abspath(os.path.join(self.cluster_dir, 'kubeconfig'))
        return self._kubectl('--kubeconfig={}'.format(kubeconfig_path), *args)

    def sleep(self, seconds_to_sleep):
        self.logger.info("Sleeping for {} seconds...".format(seconds_to_sleep))
        time.sleep(seconds_to_sleep)
        self.logger.info("Done sleeping.")

    def create_secrets(self):
        secret_path = os.path.join(self.namespace.config_dir, 'secrets')
        secret_files = self.get_config_files_in_dir(secret_path)
        for secret_file in secret_files:
            self.kubectl('create', '-f', secret_file)

    def kube_up(self):
        pass

    def kube_down(self):
        pass

    def kubectl_services(self, operation):
        # TODO: log kubectl output
        for config_file in self.get_config_files_in_dir(self.cluster_services_dir):
            try:
                self.kubectl(operation, '-f', config_file)
            except sh.ErrorReturnCode_1 as e:
                self.logger.exception("kubectl error: %s", e)

    def create_services(self):
        self.kubectl_services('create')

    def delete_services(self):
        self.kubectl_services('delete')

    def post_create(self):
        pass

    def pre_destroy(self):
        pass

    def create(self):
        self.render_provider_config()
        self.kube_up()
        self.render_services_config()
        self.create_secrets()
        self.create_services()
        self.post_create()

    def destroy(self):
        self.render_provider_config()
        self.pre_destroy()
        self.render_services_config()
        self.delete_services()
        self.kube_down()

    def scale(self):
        raise NotImplementedError("Scale operation is not implemented for this provider.")


class MetaKubeAwsCloudProvider(MetaKubeCloudProvider, AwsIngressMixin):
    ProviderName = 'aws'
    Description = 'Manage a Kubernetes cluster via AWS'

    CookbriteHostedZoneId = "Z3V39FXC7FU27B"
    AwsElbHostedZoneId = "Z3DZXE0Q79N41H"

    RegionName = "us-east-1"
    ControllerInstanceType = 'c4.xlarge'
    WorkerInstanceType = 'c4.xlarge'
    KeyName = 'cookbritedev-2014-05-06'

    def __init__(self, namespace):
        super(MetaKubeAwsCloudProvider, self).__init__(namespace)
        self.template_variables.update({
            'node_count': namespace.node_count,
            'aws_region_name': self.RegionName,
            'aws_key_name': self.KeyName,
            'aws_controller_instance_type': self.ControllerInstanceType,
            'aws_worker_instance_type': self.WorkerInstanceType,
            'celery_replica_count': namespace.node_count - 1,
            'celery_requested_memory': '7Gi',  # TODO: derive these values from instance type
            'celery_requested_cpu': '1000m',
            'celery_memory_limit': '7Gi',
            'celery_cpu_limit': '1000m',
            'service_type': 'LoadBalancer',
            'cookbrite_docker_registry': 'quay.io/cookbrite',
        })
        self.flower_external_dns = "{}-flower.cookbrite.com".format(namespace.cluster_name)
        self.rabbitmq_external_dns = "{}-rabbitmq.cookbrite.com".format(namespace.cluster_name)
        self.cluster_yaml_path = os.path.join(self.cluster_provider_dir, 'cluster.yaml')
        self.kube_aws = sh.Command('kube-aws')
        self.connection = connect_to_region(self.RegionName)

    def _get_autoscaling_group(self):
        as_connection = autoscale.connect_to_region(self.RegionName)
        asg_name_prefix = "{}-AutoScaleWorker".format(self.namespace.cluster_name)
        asg_list = [g for g in as_connection.get_all_groups() if g.name.startswith(asg_name_prefix)]
        assert len(asg_list) == 1
        return asg_list.pop()

    def _get_elastic_loadbalancer(self, name):
        elb_connection = elb.connect_to_region(self.RegionName)
        elb_list = elb_connection.get_all_load_balancers([name])
        assert len(elb_list) == 1
        return elb_list.pop()

    def update_a_record(self, stage, role, identifier):
        zone = self.connection.get_zone("cookbrite.com.")
        stage_dns_name = '{}-{}.cookbrite.com'.format(stage, role)
        try:
            zone.add_a(stage_dns_name, identifier)
        except:
            zone.update_a(stage_dns_name, identifier)
        self.logger.info("Updated DNS record '{}' to point to {}".format(stage_dns_name, identifier))

    def kube_up(self):
        cluster_ip = '127.0.0.1'
        output_lines = self.execute_command_and_log_output(self.kube_aws, ['--config', self.cluster_yaml_path, 'up'])
        for line in output_lines:
            if line.find('Controller IP') > -1:
                fields = line.split()
                cluster_ip = fields[2]

        self.update_a_record(self.namespace.release_level, self.namespace.role, cluster_ip)
        # TODO: poll instead of sleeping
        self.sleep(self.namespace.aws_kube_wait_time)

    def route53_add_or_change_alias(self, external_dns_name, internal_target):
        try:
            route53.add_alias(self.connection, self.CookbriteHostedZoneId, external_dns_name, 'A',
                              self.AwsElbHostedZoneId,
                              internal_target)
            self.logger.info("Added Route53 alias '{}'".format(external_dns_name))
        except boto.route53.exception.DNSServerError as e:
            route53.change_alias(self.connection, self.CookbriteHostedZoneId, external_dns_name, 'A',
                                 self.AwsElbHostedZoneId,
                                 internal_target)
            self.logger.info("Changed Route53 alias '{}'".format(external_dns_name))

    def route53_delete_record(self, external_dns_name, elb_identifier):
        try:
            route53.del_alias(self.connection, self.CookbriteHostedZoneId, external_dns_name, 'A',
                              self.AwsElbHostedZoneId, elb_identifier)

            self.logger.info("Deleted Route53 alias '{}'".format(external_dns_name))
        except boto.route53.exception.DNSServerError as e:
            self.logger.exception("could not delete Route53 record: %s", e)

    def post_create(self):
        # TODO: poll instead of sleeping
        self.sleep(self.namespace.aws_cluster_wait_time)
        result = self.create_load_balancers(self.namespace.cluster_name)
        flower_elb_identifier = result['flower_dns']
        flower_elb_port = result['flower_port']
        self.route53_add_or_change_alias(self.flower_external_dns, flower_elb_identifier)
        rabbitmq_elb_identifier = result['rabbitmq_dns']
        rabbitmq_port = result['rabbitmq_port']
        self.route53_add_or_change_alias(self.rabbitmq_external_dns, rabbitmq_elb_identifier)
        self.logger.info("Flower management console URL: http://{}:{}".format(self.flower_external_dns, flower_elb_port))
        self.logger.info("RabbitMQ URL: amqps://{}:{}".format(self.rabbitmq_external_dns, rabbitmq_port))

    def pre_destroy(self):
        boto_client = boto3.client('elb')
        flower_load_balancer_name = self.namespace.cluster_name + '-flower'
        load_balancers = self.get_load_balancers(boto_client, flower_load_balancer_name)
        if load_balancers:
            flower_load_balancer = load_balancers[0]
            flower_elb_identifier = flower_load_balancer['DNSName']
            self.route53_delete_record(self.flower_external_dns, flower_elb_identifier)
            self.delete_load_balancers(boto_client, flower_load_balancer_name)
        rabbitmq_load_balancer_name = self.namespace.cluster_name + '-rabbitmq'
        load_balancers = self.get_load_balancers(boto_client, rabbitmq_load_balancer_name)
        if load_balancers:
            rabbitmq_load_balancer = load_balancers[0]
            rabbitmq_elb_identifier = rabbitmq_load_balancer['DNSName']
            self.route53_delete_record(self.rabbitmq_external_dns, rabbitmq_elb_identifier)
            self.delete_load_balancers(boto_client, rabbitmq_load_balancer_name)

    def kube_down(self):
        # TODO: poll instead of sleeping
        self.sleep(self.namespace.aws_kube_wait_time)
        self.execute_command_and_log_output(self.kube_aws, ['--config', self.cluster_yaml_path, 'destroy'])
        self.sleep(self.namespace.aws_cluster_wait_time)
        # TODO: check for successful destruction

    def scale(self):
        group = self._get_autoscaling_group()
        current_node_count = group.desired_capacity
        desired_node_count = self.namespace.node_count

        if current_node_count == desired_node_count:
            self.logger.warn("Cluster is already at desired capacity of {} nodes. Not scaling.".format(
                    desired_node_count))
        else:
            if current_node_count < desired_node_count:
                self.logger.info("Desired capacity of {} is greater than current capacity of {}. Scaling out.".format(
                        desired_node_count, current_node_count))
            elif current_node_count > desired_node_count:
                self.logger.info("Desired capacity of {} is less than current capacity of {}. Scaling in.".format(
                        desired_node_count, current_node_count))

            # Scale celery pods to N-1 nodes (leaving one node to run everything else).
            # TODO: figure out how to generalize this without hard-coding, and without reinventing k8s's own bin-packing
            self.kubectl('scale', '--replicas={}'.format(desired_node_count - 1),
                         '-f', os.path.join(self.cluster_services_dir, 'celery-controller.yaml'))

            # Scale auto-scaling group to N nodes.
            # FIXME: Implement termination protection? Wait for graceful shutdown? (Or maybe just make pods crash-safe.)
            group.desired_capacity = group.min_size = group.max_size = desired_node_count
            group.update()

            self.logger.info("Waiting for instances to scale out/in...")
            start_time = time.time()
            while len(group.instances) != desired_node_count:
                if time.time() - start_time >= 60*10:
                    raise RuntimeError("Timed out after 10 minutes waiting for instances to scale.")
                else:
                    time.sleep(2)
                    group = self._get_autoscaling_group()

            asg_instances = [i.instance_id for i in group.instances]

            for service_name in ['flower', 'rabbitmq']:
                elb_name = "{}-{}".format(self.namespace.cluster_name, service_name)
                elb = self._get_elastic_loadbalancer(elb_name)
                elb_instances = [i.id for i in elb.instances]

                instances_to_add = set(asg_instances) - set(elb_instances)
                if instances_to_add:
                    self.logger.info("Going to register the following new instances in Elastic Load Balancer {}: {}"
                                     .format(elb_name, instances_to_add))
                    elb.register_instances(instances_to_add)


class MetaKubeVagrantCloudProvider(MetaKubeCloudProvider):
    ProviderName = 'vagrant'
    Description = 'Manage a Kubernetes cluster via Vagrant'

    def __init__(self, namespace):
        super(MetaKubeVagrantCloudProvider, self).__init__(namespace)
        self.template_variables.update({
            'celery_replica_count': 1,  # TODO: allow specifying multiple nodes
            'celery_requested_memory': '2Gi',  # TODO: derive these values from Vagrant config
            'celery_requested_cpu': '200m',
            'celery_memory_limit': '2Gi',
            'celery_cpu_limit': '1000m',
            'service_type': 'NodePort',
            'cookbrite_docker_registry': 'quay.io/cookbrite'
            # 'cookbrite_docker_registry': 'local-registry.cookbrite.com:5000'
        })
        self.vagrant = sh.Command('vagrant')

    def kube_up(self):
        kube_ip = "172.17.4.101"
        self.mkdir_p(self.cluster_dir)

        vagrant_dir = os.path.abspath(os.path.join(self.namespace.config_dir, 'vagrant'))
        os.chdir(vagrant_dir)
        self.execute_command_and_log_output(self.vagrant, ['box', 'update'])
        self.execute_command_and_log_output(self.vagrant, ['up'])
        self.kubectl('config', 'set-cluster', 'vagrant',
                     '--server=https://{}:443'.format(kube_ip),
                     '--certificate-authority={}/ssl/ca.pem'.format(vagrant_dir))
        self.kubectl('config', 'set-credentials', 'vagrant-admin',
                     '--certificate-authority={}/ssl/ca.pem'.format(vagrant_dir),
                     '--client-key={}/ssl/admin-key.pem'.format(vagrant_dir),
                     '--client-certificate={}/ssl/admin.pem'.format(vagrant_dir))
        self.kubectl('config', 'set-context', 'vagrant',
                     '--cluster=vagrant', '--user=vagrant-admin')
        self.kubectl('config', 'use-context', 'vagrant')
        # TODO: poll instead of sleeping
        self.sleep(self.namespace.vagrant_kube_wait_time)

    def post_create(self):
        self.sleep(self.namespace.vagrant_cluster_wait_time)
        services_json = repr(self.kubectl('get', 'nodes', '-o', 'json'))
        flower_ip_address = self.search_json(
            "items[].status.addresses[?type=='InternalIP'].address[]", services_json)
        services_json = repr(self.kubectl('get', 'services', '-o', 'json'))
        flower_node_port = self.search_json(
            "items[?metadata.name=='cookbrite-flower-service'].spec.ports[].nodePort", services_json)
        self.logger.info("Flower management console URL: http://{}:{}".format(flower_ip_address, flower_node_port))

    def kube_down(self):
        self.logger.info("Destroying vagrant cluster...")
        vagrant_dir = os.path.join(self.namespace.config_dir, 'vagrant')
        os.chdir(vagrant_dir)
        self.execute_command_and_log_output(self.vagrant, ['destroy', '-f'])
        self.logger.info("Done.")


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    defaults = dict(
        base_dir=base_dir,
        services_root=os.path.abspath(os.path.join(base_dir, "..", "..", "..")),
    )

    MetaKube.main(
        defaults,
        MetaKubeAwsCloudProvider,
        MetaKubeVagrantCloudProvider,
        description="Kubernetes cluster operations (AWS and Vagrant)",
    )


if __name__ == '__main__':
    main()
