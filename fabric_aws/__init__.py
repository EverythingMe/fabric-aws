#
# Copyright 2015 DoAT. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY DoAT ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL DoAT OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of DoAT

from __future__ import absolute_import

# noinspection PyProtectedMember
from fabric.decorators import wraps, _wrap_as_new
import boto.cloudformation
import boto.ec2
import boto.ec2.autoscale


def _list_annotating_decorator(attribute, *values):
    # based on fabric.decorators._list_annotating_decorator
    # it is exactcly the same as the original, except the fact that it generates the list lazily
    def attach_list(func):
        @wraps(func)
        def inner_decorator(*args, **kwargs):
            return func(*args, **kwargs)  # pragma: no cover

        _values = values
        # Allow for single iterable argument as well as *args
        if len(_values) == 1 and not isinstance(_values[0], basestring):
            _values = _values[0]
        setattr(inner_decorator, attribute, _values)
        # Don't replace @task new-style task objects with inner_decorator by
        # itself -- wrap in a new Task object first.
        inner_decorator = _wrap_as_new(func, inner_decorator)
        return inner_decorator

    return attach_list


def cloudformation_logical_to_physical(connection, cfn_stack_name, logical_resource_id):
    """
    Convert cloudformation logical resource name to physical resource name

    :param connection: Cloudformation connection
    :param cfn_stack_name: Cloudformation stack name
    :type cfn_stack_name: str
    :param logical_resource_id: Cloudformation logical resource id
    :type logical_resource_id: str
    :return: Physcal resource id
    :rtype: str
    """

    resource = connection.describe_stack_resource(cfn_stack_name, logical_resource_id)

    return resource.get('DescribeStackResourceResponse', {}). \
        get('DescribeStackResourceResult', {}). \
        get('StackResourceDetail', {}). \
        get('PhysicalResourceId')


def autoscaling_group_instances(autoscale_connection, ec2_connection, autoscaling_group_name):
    """
    Return a list of Instance objects for all instances inside autoscaling group `autoscaling_group_name`

    :param autoscale_connection: Autoscaling group connection
    :param ec2_connection: Ec2 connection
    :param autoscaling_group_name: Autoscaling group name
    :type autoscaling_group_name: str
    :return: List of `Instance` objects
    :rtype: list[boto.ec2.instance.Instance]
    """

    asg = autoscale_connection.get_all_groups(names=[autoscaling_group_name])[0]

    reservations = ec2_connection.get_all_instances(instance_ids=[instance.instance_id for instance in asg.instances])
    return [instance for reservation in reservations for instance in reservation.instances]


def cloudformation_autoscaling_group_generator(region, cfn_stack_name, asg_resource_name,
                                               hostname_attribute='public_dns_name'):
    """
    Hosts generator for running a task on all instances inside an autoscaling group that is a part of a CFN stack
    Please decorate your functions with `cloudformation_autoscaling_group`

    :param region: AWS region
    :type region: str
    :param cfn_stack_name: Cloudformation stack name
    :type cfn_stack_name: str
    :param asg_resource_name: Autoscaling group logical resource name inside `cfn_stack_name`
    :type asg_group_name: str
    :param hostname_attribute: `boto.ec2.instance.Instance` attribute to use as hostname for fabric connection
    """

    cfn = boto.cloudformation.connect_to_region(region)
    physical_resource_id = cloudformation_logical_to_physical(cfn, cfn_stack_name, asg_resource_name)

    for hostname in autoscaling_group_generator(region, physical_resource_id, hostname_attribute):
        yield hostname


def autoscaling_group_generator(region, autoscaling_group_name, hostname_attribute='public_dns_name'):
    """
    Hosts generator for running a task on all instances inside an autoscaling group
    Please decorate your functions with `autoscaling_group`

    :param region: AWS region
    :type region: str
    :param autoscaling_group_name: Autoscaling group logical resource name inside `cfn_stack_name`
    :type autoscaling_group_name: str
    :param hostname_attribute: `boto.ec2.instance.Instance` attribute to use as hostname for fabric connection
    """

    autoscale = boto.ec2.autoscale.connect_to_region(region)
    ec2 = boto.ec2.connect_to_region(region)

    instances = autoscaling_group_instances(autoscale, ec2, autoscaling_group_name)

    for instance in instances:
        yield getattr(instance, hostname_attribute)


@wraps(autoscaling_group_generator)
def autoscaling_group(*args, **kwargs):
    """
    Fabric decorator for running a task on all instances inside an autoscaling group

    :param region: AWS region
    :type region: str
    :param autoscaling_group_name: Autoscaling group logical resource name inside `cfn_stack_name`
    :type autoscaling_group_name: str
    :param hostname_attribute: `boto.ec2.instance.Instance` attribute to use as hostname for fabric connection
    """

    return _list_annotating_decorator('hosts', autoscaling_group_generator(*args, **kwargs))


@wraps(cloudformation_autoscaling_group_generator)
def cloudformation_autoscaling_group(*args, **kwargs):
    """
    Decorator for running a task on all instances inside an autoscaling group that is a part of a CFN stack

    :param region: AWS region
    :type region: str
    :param cfn_stack_name: Cloudformation stack name
    :type cfn_stack_name: str
    :param asg_resource_name: Autoscaling group logical resource name inside `cfn_stack_name`
    :type asg_group_name: str
    :param hostname_attribute: `boto.ec2.instance.Instance` attribute to use as hostname for fabric connection
    """

    return _list_annotating_decorator('hosts', cloudformation_autoscaling_group_generator(*args, **kwargs))


__all__ = ['cloudformation_autoscaling_group', 'autoscaling_group']
