#!/usr/bin/env python


from __future__ import print_function, absolute_import

import os

import boto3
import sh
import sys

import yaml


class ScaleCluster(object):
    def __init__(self):
        pass

    def usage(self):
        print("Usage: ")
        print("    scale_cluster.py <kubeconfig_path> [additional_nodes]")
        print()
        print(
            "    Resize AWS kubernetes cluster removing nodes that have no pods; or if additional_nodes is specified, "
            "will add the number of instances specified.")

    def main(self):
        if len(sys.argv) < 2:
            self.usage()
            sys.exit(1)
        kubeconfig_path = sys.argv[1]
        if len(sys.argv) == 3:
            additional_instances = int(sys.argv[2])
        else:
            additional_instances = -1
        kubectl = sh.Command('kubectl')
        nodes_output = kubectl('--kubeconfig', kubeconfig_path, 'get', 'nodes', '-o', 'wide')
        pods_output = kubectl('--kubeconfig', kubeconfig_path, 'get', 'pods', '-o', 'wide')
        nodes_names = []
        pod_names = []
        for line in nodes_output.split('\n')[1:]:
            words = line.strip().split()
            if len(words):
                node_name = words[0].strip()
                if node_name:
                    nodes_names.append(node_name)
        for line in pods_output.split('\n')[1:]:
            words = line.strip().split()
            if len(words):
                pod_name = words[5].strip()
                if pod_name:
                    pod_names.append(pod_name)
        pods = {}
        empty_nodes = {}
        for pod_name in pod_names:
            pods[pod_name] = pod_name
        print("Active nodes:")
        for pod_name in pod_names:
            print(pod_name)
        print("Empty nodes:")
        for node_name in nodes_names:
            if node_name not in pods:
                empty_nodes[node_name] = node_name
                print(node_name)
        if additional_instances < 0:
            self.scale_down(kubeconfig_path, pods, empty_nodes)
        else:
            self.scale_up(kubeconfig_path, additional_instances)

    def splitall(self, path):
        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    def get_cluster_name(self, kubeconfig_path):
        cluster_name = self.splitall(kubeconfig_path)[-2]
        return cluster_name

    def scale_down(self, kubeconfig_path, active_names, inactive_names):
        autoscaling_client = boto3.client('autoscaling')

        response = autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[],
        )
        autoscaling_groups = response['AutoScalingGroups']
        cluster_name = self.get_cluster_name(kubeconfig_path)
        print(cluster_name)
        for group in autoscaling_groups:
            autoscaling_group_name = group['AutoScalingGroupName']
            if autoscaling_group_name.startswith(cluster_name):
                print(autoscaling_group_name)
                min_size = group['MinSize']
                max_size = group['MaxSize']
                print("  MinSize : {}".format(min_size))
                print("  MaxSize : {}".format(max_size))
                instances = group['Instances']
                self.protect_instances_and_scale(autoscaling_client, autoscaling_group_name, instances, active_names,
                                                 inactive_names)

    def scale_up(self, kubeconfig_path, additional_instances):
        autoscaling_client = boto3.client('autoscaling')

        response = autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[],
        )
        autoscaling_groups = response['AutoScalingGroups']
        cluster_name = self.get_cluster_name(kubeconfig_path)
        print(cluster_name)
        for group in autoscaling_groups:
            autoscaling_group_name = group['AutoScalingGroupName']
            if autoscaling_group_name.startswith(cluster_name):
                print(autoscaling_group_name)
                min_size = group['MinSize']
                max_size = group['MaxSize']
                print("  MinSize : {}".format(min_size))
                print("  MaxSize : {}".format(max_size))
                instances = group['Instances']
                new_min_size = min_size + additional_instances
                new_max_size = min_size + additional_instances
                if min_size != new_min_size:
                    response = autoscaling_client.update_auto_scaling_group(
                            AutoScalingGroupName=autoscaling_group_name,
                            MinSize=new_min_size,
                            MaxSize=new_max_size,
                    )
                    print(
                            "Set autoscaling group '{}' to min_size {} and max_size {}. "
                            "If size was increased, instances will start launching soon.".format(
                                    autoscaling_group_name, new_min_size, new_max_size))
                else:
                    print("No new instances requested, not scaling.")

    def protect_instances_and_scale(self, autoscaling_client, autoscaling_group_name, instances, active_names,
                                    inactive_names):
        active_instance_ids = self.get_instance_ids(active_names)
        inactive_instance_ids = self.get_instance_ids(inactive_names)
        print("Active instances: {}".format(active_instance_ids))
        print("Inactive instances: {}".format(inactive_instance_ids))
        if active_instance_ids:
            response = autoscaling_client.set_instance_protection(
                    InstanceIds=active_instance_ids,
                    AutoScalingGroupName=autoscaling_group_name,
                    ProtectedFromScaleIn=True
            )
        if inactive_instance_ids:
            response = autoscaling_client.set_instance_protection(
                    InstanceIds=inactive_instance_ids,
                    AutoScalingGroupName=autoscaling_group_name,
                    ProtectedFromScaleIn=False
            )
        min_size = len(active_names)
        max_size = min_size
        if inactive_instance_ids:
            response = autoscaling_client.update_auto_scaling_group(
                    AutoScalingGroupName=autoscaling_group_name,
                    MinSize=min_size,
                    MaxSize=max_size,
            )
            print(
                    "Set autoscaling group '{}' to min_size {} and max_size {}. "
                    "If size was reduced, instances will start terminating soon.".format(
                            autoscaling_group_name, min_size, max_size))
        else:
            print("No inactive instances, not scaling.")

    def get_instance_ids(self, names):
        ec2 = boto3.resource('ec2')
        instances = ec2.instances.filter(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instance_ids = []
        for instance in instances:
            if instance.private_dns_name in names:
                instance_ids.append(instance.instance_id)
        return instance_ids

    @classmethod
    def parse_args(cls, defaults, *layer_classes, **kwargs):
        parser = argparse.ArgumentParser(
                description=kwargs.pop('description', "Kubernetes cluster operations"))

        defaults = defaults or {}
        # defaults.setdefault('base_dir', os.path.abspath(os.path.dirname(__file__)))

        parser.set_defaults(
                **defaults
        )
        parser.add_argument(
                '--config-dir', '-C',
                default='.',
                help="Configuration directory (defaults to current working directory)")

        namespace = parser.parse_args()
        # namespace.logger = cls.configure_logging(namespace)


if __name__ == "__main__":
    ScaleCluster().main()
