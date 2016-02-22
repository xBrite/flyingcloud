#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import json
import os
import boto3 as boto
import botocore
import sh
import time

SECURITY_GROUP_DELETION_RETRIES = 3
SECURITY_GROUP_DELETION_WAIT_TIME_SECONDS = 60


# TODO
# - nothing so far

class AwsIngressMixin(object):
    def get_security_groups(self, boto_client, cluster_name, vpc_id):
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]},
                   {'Name': 'group-name', 'Values': [cluster_name]}]
        response = boto_client.describe_security_groups(Filters=filters)
        security_groups = response['SecurityGroups']
        return security_groups

    def get_worker_security_group(self, boto_client, cluster_name, vpc_id):
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
        response = boto_client.describe_security_groups(Filters=filters)
        security_groups = response['SecurityGroups']
        worker_security_groups = []
        for security_group in security_groups:
            security_group_name = security_group['GroupName']
            if (security_group_name.startswith(cluster_name) and
                        security_group_name.find('Worker') > 0):
                worker_security_groups.append(security_group)
        return worker_security_groups[0]

    def delete_security_groups_if_necessary(self, boto_client, cluster_name, vpc_id):
        security_groups = self.get_security_groups(boto_client, cluster_name, vpc_id)
        if len(security_groups) > 0:
            for security_group in security_groups:
                security_group_id = security_group['GroupId']
                deleted = False
                retries = SECURITY_GROUP_DELETION_RETRIES
                while not deleted and retries > 0:
                    try:
                        boto_client.delete_security_group(GroupId=security_group_id)
                        deleted = True
                    except botocore.exceptions.ClientError as e:
                        time.sleep(SECURITY_GROUP_DELETION_WAIT_TIME_SECONDS)
                        retries -= 1
                        if retries > 0:
                            print(
                                "Can't delete security group {} because of {}... sleeping {} seconds, will retry {} more times.".format(
                                    security_group_id, e, SECURITY_GROUP_DELETION_WAIT_TIME_SECONDS, retries))
                        else:
                            print("Failed to delete security group {}".format(security_group_id))
            if deleted:
                print("Deletion successful.")

    def create_security_group(self, boto_client, cluster_name, vpc_id, external_ports, internal_ports):
        worker_security_group = self.get_worker_security_group(boto_client, cluster_name, vpc_id)
        worker_security_group_id = worker_security_group['GroupId']
        security_groups = self.get_security_groups(boto_client, cluster_name, vpc_id)
        if security_groups:
            security_group_id = security_groups[0]['GroupId']
            for port in internal_ports:
                ip_permissions = [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': port,
                        'ToPort': port,
                        'UserIdGroupPairs': [
                            {
                                'GroupId': security_group_id
                            },
                        ],
                    },
                ]
                try:
                    response = boto_client.revoke_security_group_ingress(GroupId=worker_security_group_id,
                                                                     IpPermissions=ip_permissions)
                except botocore.exceptions.ClientError as e:
                    print("Could not revoke ingress for {} {}".format(worker_security_group_id, ip_permissions))
        self.delete_security_groups_if_necessary(boto_client, cluster_name, vpc_id)

        response = boto_client.create_security_group(GroupName=cluster_name,
                                                     Description='{} security group'.format(cluster_name),
                                                     VpcId=vpc_id)
        security_group_id = response['GroupId']

        for port in external_ports:
            boto_client.authorize_security_group_ingress(GroupId=security_group_id, IpProtocol='tcp', FromPort=port,
                                                         ToPort=port, CidrIp='0.0.0.0/0')
        for port in internal_ports:
            ip_permissions = [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': port,
                        'ToPort': port,
                        'UserIdGroupPairs': [
                            {
                                'GroupId':  security_group_id
                            },
                        ],
                    },
                ]
            boto_client.authorize_security_group_ingress(GroupId=worker_security_group_id,
                                                         IpPermissions=ip_permissions)
        return security_group_id

    def get_load_balancers(self, boto_client, load_balancer_name):
        load_balancers = []
        try:
            response = boto_client.describe_load_balancers(LoadBalancerNames=[load_balancer_name])
            load_balancers = response['LoadBalancerDescriptions']
        except botocore.exceptions.ClientError as e:
            pass
        return load_balancers

    def delete_load_balancers(self, boto_client, load_balancer_name):
        load_balancers = self.get_load_balancers(boto_client, load_balancer_name)
        if len(load_balancers) > 0:
            for load_balancer in load_balancers:
                boto_client.delete_load_balancer(LoadBalancerName=load_balancer['LoadBalancerName'])

    def create_elb(self, elb_client, load_balancer_name, subnets, security_group_id, instance_ids, listeners,
                   health_check):
        security_groups = [security_group_id]
        elb_client.create_load_balancer(LoadBalancerName=load_balancer_name,
                                        Listeners=listeners,
                                        SecurityGroups=security_groups,
                                        Subnets=subnets)
        elb_client.configure_health_check(LoadBalancerName=load_balancer_name, HealthCheck=health_check)
        instances = [{'InstanceId': instance_id} for instance_id in instance_ids]
        elb_client.register_instances_with_load_balancer(LoadBalancerName=load_balancer_name, Instances=instances)
        load_balancer = self.get_load_balancers(elb_client, load_balancer_name)[0]
        load_balancer_dns_name = load_balancer['DNSName']
        return load_balancer_dns_name

    def configure_elb_for_websockets(self, elb_client, load_balancer_name, port):
        ssl_websockets_policy = load_balancer_name + '-ssl-websockets-policy'
        response = elb_client.create_load_balancer_policy(
                LoadBalancerName=load_balancer_name,
                PolicyName=ssl_websockets_policy,
                PolicyTypeName='ProxyProtocolPolicyType',
                PolicyAttributes=[
                    {
                        'AttributeName': 'ProxyProtocol',
                        'AttributeValue': 'True'
                    },
                ]
            )
        response = elb_client.set_load_balancer_policies_for_backend_server(
                LoadBalancerName=load_balancer_name,
                InstancePort=port,
                PolicyNames=[
                    ssl_websockets_policy,
                ]
            )

    def elb_flower(self, elb_client, cluster_name, subnets, security_group_id, instance_ids, ssl_cert_arn):
        load_balancer_name = cluster_name + '-flower'
        port = 31555
        health_check = {
            'Target': 'TCP:31555',
            'Interval': 30,
            'Timeout': 5,
            'UnhealthyThreshold': 2,
            'HealthyThreshold': 10
        }

        listeners = [
            {
                'Protocol': 'SSL',
                'LoadBalancerPort': port,
                'InstanceProtocol': 'TCP',
                'InstancePort': port,
                'SSLCertificateId': ssl_cert_arn
            }
        ]
        load_balancer_dns_name = self.create_elb(elb_client, load_balancer_name, subnets, security_group_id,
                               instance_ids, listeners, health_check)
        self.configure_elb_for_websockets(elb_client, load_balancer_name, port)
        return load_balancer_dns_name

    def elb_rabbitmq(self, elb_client, cluster_name, subnets, security_group_id, instance_ids, ssl_cert_arn):
        load_balancer_name = cluster_name + '-rabbitmq'
        health_check = {
            'Target': 'TCP:31672',
            'Interval': 30,
            'Timeout': 5,
            'UnhealthyThreshold': 2,
            'HealthyThreshold': 10
        }
        listeners = [
            {
                'Protocol': 'ssl',
                'LoadBalancerPort': 31673,
                'InstanceProtocol': 'tcp',
                'InstancePort': 31672,
                'SSLCertificateId': ssl_cert_arn
            }
        ]
        return self.create_elb(elb_client, load_balancer_name, subnets, security_group_id,
                               instance_ids, listeners, health_check)

    def get_vpc_id(self, client, cluster_name):
        response = client.describe_vpcs()
        vpcs = response['Vpcs']
        for vpc in vpcs:
            for tag in vpc["Tags"]:
                if tag["Key"] == "KubernetesCluster" and tag["Value"] == cluster_name:
                    return vpc["VpcId"]
        return None

    def get_subnet_ids(self, client, vpc_id):
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
        response = client.describe_subnets(Filters=filters)
        subnets = response['Subnets']
        result = [subnet['SubnetId'] for subnet in subnets]
        return result

    def get_instances(self, client, vpc_id):
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
        result = client.describe_instances(Filters=filters)
        reservations = result['Reservations']
        instances = []
        for reservation in reservations:
            instances += reservation['Instances']
        return instances

    def get_instance_ids(self, client, vpc_id, node_internal_dns_names):
        instance_ids = {}
        instances = self.get_instances(client, vpc_id)
        for instance in instances:
            for node_internal_dns_name in node_internal_dns_names:
                for network_interface in instance['NetworkInterfaces']:
                    if network_interface['PrivateDnsName'] == node_internal_dns_name:
                        instance_ids[instance['InstanceId']] = 1
        return instance_ids.keys()

    def get_pod_internal_dns_names(self, cluster_name):
        kubectl = sh.Command('kubectl')
        config_dir = os.path.abspath(os.path.join(os.getcwd(), 'clusters', cluster_name))
        kubeconfig_path = os.path.join(config_dir, 'kubeconfig')
        result = kubectl('--kubeconfig={}'.format(kubeconfig_path), 'get', 'pods', '-o', 'json')
        pod_list = json.loads(str(result))
        pods = pod_list["items"]
        node_internal_dns_names = []
        for pod in pods:
            node_name = pod["spec"]["nodeName"]
            node_internal_dns_names.append(node_name)
        return node_internal_dns_names

    def create_load_balancers(self, cluster_name):
        # TODO
        # - make this create a single load balancer, returning dns name and port
        ingress = AwsIngressMixin()
        ssl_cert_arn = 'arn:aws:iam::565362801595:server-certificate/star_cookbrite_com_2016'
        region = "us-east-1"
        ec2_client = boto.client('ec2')
        vpc_id = ingress.get_vpc_id(ec2_client, cluster_name)
        subnets = ingress.get_subnet_ids(ec2_client, vpc_id)
        node_internal_dns_names = ingress.get_pod_internal_dns_names(cluster_name)
        instance_ids = ingress.get_instance_ids(ec2_client, vpc_id, node_internal_dns_names)
        flower_port = 31555
        rabbitmq_internal_port = 31672
        rabbitmq_external_port = 31673
        internal_ports = [flower_port, rabbitmq_internal_port]
        external_ports = [flower_port, rabbitmq_external_port]
        elb_client = boto.client('elb')
        ingress.delete_load_balancers(elb_client, cluster_name + '-flower')
        ingress.delete_load_balancers(elb_client, cluster_name + '-rabbitmq')
        security_group_id = ingress.create_security_group(ec2_client, cluster_name, vpc_id, external_ports, internal_ports)
        elb_flower_dns_name = ingress.elb_flower(elb_client, cluster_name, subnets, security_group_id, instance_ids,
                                                 ssl_cert_arn)
        elb_rabbitmq_dns_name = ingress.elb_rabbitmq(elb_client, cluster_name, subnets, security_group_id, instance_ids,
                                                     ssl_cert_arn)
        result = {
            'flower_dns': elb_flower_dns_name,
            'flower_port': flower_port,
            'rabbitmq_dns': elb_rabbitmq_dns_name,
            'rabbitmq_port': rabbitmq_external_port
        }
        return result


if __name__ == '__main__':
    print(AwsIngressMixin().create_load_balancers('dev-lectern'))
