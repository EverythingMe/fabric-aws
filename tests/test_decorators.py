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

from fabric_aws import *
from fabric.api import task
import unittest
import mock


# noinspection PyUnusedLocal
def mock_cloudformation_logical_to_physical(connection, cfn_stack_name, logical_resource_id):
    return "{}-physical".format(logical_resource_id)

# noinspection PyUnusedLocal
def mock_autoscaling_group_instances(autoscale_connection, ec2_connection, autoscaling_group_name):
    return [mock.Mock(public_dns_name='a.b.c', private_ip_address='10.0.0.1'),
            mock.Mock(public_dns_name='e.f.g', private_ip_address='10.0.0.2')]


@mock.patch('boto.cloudformation.connect_to_region', new=mock.MagicMock())
@mock.patch('boto.ec2.connect_to_region', new=mock.MagicMock())
@mock.patch('boto.ec2.autoscale.connect_to_region', new=mock.MagicMock())
@mock.patch('fabric_aws.cloudformation_logical_to_physical', mock_cloudformation_logical_to_physical)
@mock.patch('fabric_aws.autoscaling_group_instances', mock_autoscaling_group_instances)
class TestDecorators(unittest.TestCase):
    def test_cloudformation_logical_to_physical(self):
        @cloudformation_autoscaling_group('region', 'stack-name',
                                          'logical-autoscaling-group-name', 'private_ip_address')
        @task
        def dummy():
            pass

        self.assertListEqual(['10.0.0.1', '10.0.0.2'], list(dummy.hosts))

    def test_autoscaling_group(self):
        @autoscaling_group('region', 'autoscaling-group-name')
        @task
        def dummy():
            pass

        self.assertListEqual(['a.b.c', 'e.f.g'], list(dummy.hosts))
