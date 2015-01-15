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

from fabric_aws import autoscaling_group_instances, cloudformation_logical_to_physical
import unittest
import mock


class TestBotoIntegration(unittest.TestCase):
    def test_autoscaling_group_instances(self):
        ec2_instances_a = [
            mock.Mock(instance_id='i-00000001', public_dns_name='a.a.a', private_ip_address='10.0.0.1'),
            mock.Mock(instance_id='i-00000002', public_dns_name='b.b.b', private_ip_address='10.0.0.2')
        ]

        ec2_instances_b = [
            mock.Mock(instance_id='i-00000003', public_dns_name='c.c.c', private_ip_address='10.0.0.3'),
            mock.Mock(instance_id='i-00000004', public_dns_name='d.d.d', private_ip_address='10.0.0.4')
        ]

        autoscaling_connection = mock.MagicMock(**{
            'get_all_groups.return_value': [mock.MagicMock(instances=[mock.Mock(instance_id='i-00000001'),
                                                                      mock.Mock(instance_id='i-00000002'),
                                                                      mock.Mock(instance_id='i-00000003'),
                                                                      mock.Mock(instance_id='i-00000004')])]
        })

        ec2_connection = mock.MagicMock(**{
            'get_all_instances.return_value': [mock.MagicMock(instances=ec2_instances_a),
                                               mock.MagicMock(instances=ec2_instances_b)]
        })

        self.assertListEqual(
            ec2_instances_a + ec2_instances_b,
            autoscaling_group_instances(autoscaling_connection, ec2_connection, 'dummy-asg-name')
        )

        autoscaling_connection.get_all_groups.assert_called_once_with(names=['dummy-asg-name'])
        ec2_connection.get_all_instances.assert_called_once_with(instance_ids=['i-00000001',
                                                                               'i-00000002',
                                                                               'i-00000003',
                                                                               'i-00000004'])

    def test_cloudformation_logical_to_physical(self):
        cfn_connection = mock.MagicMock(**{
            'describe_stack_resource.return_value': {
                'DescribeStackResourceResponse': {
                    'DescribeStackResourceResult': {
                        'StackResourceDetail': {
                            'PhysicalResourceId': 'my-awesome-physical-resource'
                        }
                    }
                }
            }
        })

        self.assertEqual(
            'my-awesome-physical-resource',
            cloudformation_logical_to_physical(cfn_connection, 'stack-name', 'resource-name')
        )

        cfn_connection.describe_stack_resource.assert_called_once_with('stack-name', 'resource-name')
