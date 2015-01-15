[![Build Status](https://travis-ci.org/EverythingMe/fabric-aws.svg?branch=master)](https://travis-ci.org/EverythingMe/fabric-aws)

# Fabric AWS integration

Ever used pychef's fabric integration and loved it?  
This project aims to integrate AWS with fabric. You can decorate your fabric tasks to run on an Autoscaling group (which can also be a part of an Cloudformation stack)

## Installation
`pip install fabric-aws`

## Example fabfile

```python
from fabric.api import *
from fabric_aws import *


@autoscaling_group('us-east-1', 'my-autoscaling-group')
@task
def uptime_asg():
    run('uptime')

@cloudformation_autoscaling_group('us-east-1', 'my-cloudformation', 'AutoScalingGroup')
@task
def uptime_cfn():
    run('uptime')
```
