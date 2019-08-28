#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: 2019 Atlassian
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

import json
import sys
from ansible.module_utils.opsgenie import request, pfilter, statcheck, checkop
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: opsgenie_integration
short_description: Manage Opsgenie integrations.
description:
    - Manage Opsgenie teams.
version_added: "FIXME"
author:
    - "Steve Smith (@tarka)"

options:
  operation:
    required: true
    aliases: [ command ]
    choices: [ create ]
    description:
      - The operation to perform.

  key:
    aliases: [ apikey ]
    required: true
    description:
      - A valid API key. See "API key management" in Settings in the Opsgenie web console.

  region:
    required: false
    choices: [ US, EU ]
    default: US
    description:
      - The region your account is in; US or EU. US is the default.

  name:
    required: true
    description:
      - The integration name this operation applies to.

  type:
    required: false
    description:
      - The integration type; required  when creating an integration.

  ownner:
    required: false
    description:
      - The team that owns the integration; required  when creating an integration.

  parameters:
    required: false
    description:
      - A free-form map of additional parameters. These depend on the type of integration, and are converted into JSON. See the Opsgenie Integration API documentation for the required parameters.
'''

EXAMPLES = '''
# Create a CloudWatch integration for an existing group.
- opsgenie_integration:
    operation: create
    name: 'CW'
    type: "CloudWatch"
    owner: "integration_group"
    key: "{{ my_opsgenie_key }}"
'''

######################################################################
# Operations:
# Each op should take a base URL, key and the params. It should return
# (body, changed, failed). See 'Dispatch' below for the invocation.

# Some parameters are required depending on the operation:
OP_REQUIRED = dict(
    create=['type', 'owner'],
)


def create(module):
    data = pfilter(module.params, ['name', 'type'])
    data.update(module.params.get('parameters') or {})
    data['ownerTeam'] = {
        'name': module.params['owner']
    }
    endpoint = '/integrations'
    info, body  = request(module, endpoint, data=data, method='POST')

    return statcheck(info, body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            operation=dict(choices=['create'],
                           aliases=['command'], required=True),
            key=dict(aliases=['apikey'], required=True, no_log=True),
            region=dict(required=False, default='US'),
            name=dict(required=True),

            type=dict(required=False),
            owner=dict(required=False),
            parameters=dict(required=False, type='dict'),
        ),
        supports_check_mode=False
    )
    checkop(module, OP_REQUIRED)

    op = module.params['operation']

    # Dispatch:
    # FIXME: This could be a getattr lookup, but it wasn't playing
    # well with the Ansible wrapper, so this works for now.
    if op == 'create':
        body, changed, fail = create(module)
    else:
        return module.fail_json(msg="Unknown operation")

    module.exit_json(changed=changed, meta=body)

if __name__ == '__main__':
    main()
