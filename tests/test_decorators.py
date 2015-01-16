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

from fabric_aws import *
from fabric.api import task
import unittest
import mock
from test_boto_integration import mock_environment


class TestDecorators(unittest.TestCase):
    def test_laziness(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            # noinspection PyUnusedLocal
            @cloudformation_autoscaling_group('region', 'stack-name',
                                              'logical-autoscaling-group-name', 'private_ip_address')
            @task
            def dummy1():
                pass

            # noinspection PyUnusedLocal
            @autoscaling_group('region', 'autoscaling-group-name')
            @task
            def dummy2():
                pass

            # noinspection PyUnusedLocal
            @ec2('region', instance_ids=['i-00000001', 'i-00000002', 'i-00000003', 'i-00000004'])
            @task
            def dummy3():
                pass

        self.assertFalse(mock_ec2.connect_to_region.called)
        self.assertFalse(mock_ec2.autoscale.return_value.connect_to_region.called)
        self.assertFalse(mock_cloudformation.connect_to_region.called)

    def test_cloudformation_autoscaling_group(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            @cloudformation_autoscaling_group('region', 'stack-name',
                                              'logical-autoscaling-group-name', 'private_ip_address')
            @task
            def dummy():
                pass

            hosts = list(dummy.hosts)

        self.assertListEqual(
            ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4'],
            hosts
        )

    def test_autoscaling_group(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            @autoscaling_group('region', 'autoscaling-group-name')
            @task
            def dummy():
                pass

            hosts = list(dummy.hosts)

        self.assertListEqual(
            ['a.a.a', 'b.b.b', 'c.c.c', 'd.d.d'],
            hosts
        )

    def test_ec2(self):
        mock_cloudformation, mock_ec2 = mock_environment()

        with mock.patch('boto.ec2', mock_ec2), mock.patch('boto.cloudformation', mock_cloudformation):
            @ec2('region', instance_ids=['i-00000001', 'i-00000002', 'i-00000003', 'i-00000004'])
            @task
            def dummy():
                pass

            hosts = list(dummy.hosts)

        self.assertListEqual(
            ['a.a.a', 'b.b.b', 'c.c.c', 'd.d.d'],
            hosts
        )
