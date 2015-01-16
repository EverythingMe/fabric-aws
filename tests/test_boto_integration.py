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

from fabric_aws import autoscaling_group_instance_ids, cloudformation_logical_to_physical, ec2_generator
import unittest
import mock

def mock_environment():
    mock_autoscale_connection = mock.MagicMock(**{
        'get_all_groups.return_value': [mock.MagicMock(instances=[mock.Mock(instance_id='i-00000001'),
                                                                  mock.Mock(instance_id='i-00000002'),
                                                                  mock.Mock(instance_id='i-00000003'),
                                                                  mock.Mock(instance_id='i-00000004')])]
    })
    mock_autoscale = mock.MagicMock(**{'connect_to_region.return_value': mock_autoscale_connection})

    mock_ec2_connection = mock.MagicMock(**{
        'get_all_instances.return_value': [
            mock.MagicMock(instances=[
                mock.Mock(instance_id='i-00000001', public_dns_name='a.a.a', private_ip_address='10.0.0.1'),
                mock.Mock(instance_id='i-00000002', public_dns_name='b.b.b', private_ip_address='10.0.0.2')]),
            mock.MagicMock(instances=[
                mock.Mock(instance_id='i-00000003', public_dns_name='c.c.c', private_ip_address='10.0.0.3'),
                mock.Mock(instance_id='i-00000004', public_dns_name='d.d.d', private_ip_address='10.0.0.4')])
        ]
    })
    mock_ec2 = mock.MagicMock(**{'connect_to_region.return_value': mock_ec2_connection, 'autoscale': mock_autoscale})

    mock_cloudformation_connection = mock.MagicMock(**{
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
    mock_cloudformation = mock.MagicMock(**{'connect_to_region.return_value': mock_cloudformation_connection})

    return mock_cloudformation, mock_ec2


class TestBotoIntegration(unittest.TestCase):
    def test_autoscaling_group_instances(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            instance_ids = autoscaling_group_instance_ids('us-east-1', 'dummy-asg-name')

        mock_ec2.autoscale.connect_to_region.assert_called_once_with('us-east-1')

        mock_autoscale_connection = mock_ec2.autoscale.connect_to_region.return_value
        mock_autoscale_connection.get_all_groups.assert_called_once_with(names=['dummy-asg-name'])

        self.assertListEqual(
            ['i-00000001', 'i-00000002', 'i-00000003', 'i-00000004'],
            instance_ids
        )

    def test_cloudformation_logical_to_physical(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            physical = cloudformation_logical_to_physical('us-east-1', 'stack-name', 'resource-name')

        mock_cloudformation.connect_to_region.assert_called_once_with('us-east-1')

        mock_cfn_connection = mock_cloudformation.connect_to_region.return_value
        mock_cfn_connection.describe_stack_resource.assert_called_once_with('stack-name', 'resource-name')

        self.assertEqual(
            'my-awesome-physical-resource',
            physical
        )

    def test_ec2_generator(self):
        mock_cloudformation, mock_ec2 = mock_environment()
        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            instance_hosts = list(ec2_generator('us-east-1',
                                                instance_ids=['i-00000001', 'i-00000002', 'i-00000003', 'i-00000004']))

        mock_ec2.connect_to_region.assert_called_once_with('us-east-1')

        mock_ec2_connection = mock_ec2.connect_to_region.return_value
        mock_ec2_connection.get_all_instances.assert_called_once_with(
            instance_ids=['i-00000001', 'i-00000002', 'i-00000003', 'i-00000004'])

        self.assertListEqual(
            ['a.a.a', 'b.b.b', 'c.c.c', 'd.d.d'],
            instance_hosts
        )
