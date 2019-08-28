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
module: opsgenie_team
short_description: Create and manage Opsgenie teams.
description:
    - Create and manage Opsgenie teams.
version_added: "FIXME"
author:
    - "Steve Smith (@tarka)"

options:
  operation:
    required: true
    aliases: [ command ]
    choices: [ create, delete, add_member, remove_member ]
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
      - The team name this operation applies to.

  description:
    required: false
    description:
      - The description for the team; only applies to create and update operations.

  user:
    required: false
    description:
      - The team member to add or remove. Required for those operations.

  role:
    required: false
    description:
      - The role for the team member being added. Required for that operation.
'''

EXAMPLES = '''
# Create an Opsgenie team
- opsgenie_team:
    operation: create
    name: 'dummy_group'
    description: "A dummy Group"
    key: "{{ my_opsgenie_key }}"
  register: team_meta

# Delete the group
- opsgenie_team:
    operation: delete
    name: 'dummy_group'
    key: "{{ my_opsgenie_key }}"

# Add a user to a team as admin
- opsgenie_team:
  operation: add_member
    name: 'member_group'
    user: 'ssmith+opsgenie@haltcondition.net'
    role: 'admin'
    key: "{{ my_opsgenie_key }}"

# Remove a user from a team
- opsgenie_team:
    operation: remove_member
    name: 'member_group'
    user: 'ssmith+opsgenie@haltcondition.net'
    key: "{{ my_opsgenie_key }}"

'''

######################################################################
# Operations:
# Each op should take a base URL, key and the params. It should return
# (body, changed, failed). See 'Dispatch' below for the invocation.

# Some parameters are required depending on the operation:
OP_REQUIRED = dict(
    create=[],
    delete=[],
    add_member=['user', 'role'],
    remove_member=['user'],
)


def create(module):
    # FIXME: Add members, or leave to individual calls?
    data = pfilter(module.params, ['name', 'description'])
    endpoint = '/teams'
    info, body  = request(module, endpoint, data=data, method='POST')

    if info['status'] == 409:
        # Conflict; assume team-name already exists
        return body, False, False
    else:
        return statcheck(info, body)


def delete(module):
    endpoint = '/teams/' + module.params['name'] + '?identifierType=name'
    info, body = request(module, endpoint, method='DELETE')
    return statcheck(info, body)


def add_member(module):
    # TODO: Add always returns 'Added', even if the user was already
    # a member. Ideally we should check for this and quit with
    # changed=false.
    endpoint = '/teams/' + module.params['name'] + '/members?teamIdentifierType=name'
    data = {
        'user': {
            'username': module.params['user']
        },
        'role': module.params['role']
    }

    info, body  = request(module, endpoint, data=data, method='POST')

    return statcheck(info, body)


def remove_member(module):
    endpoint = '/teams/' + module.params['name'] + '/members/' + module.params['user'] + '?teamIdentifierType=name'
    info, body  = request(module, endpoint, method='DELETE')
    return statcheck(info, body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            operation=dict(choices=['create', 'delete', 'add_member', 'remove_member'],
                           aliases=['command'], required=True),
            key=dict(aliases=['apikey'], required=True, no_log=True),
            region=dict(required=False, default='US'),
            name=dict(required=True),

            description=dict(required=False),
            user=dict(required=False),
            role=dict(required=False),
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
    elif op == 'delete':
        body, changed, fail = delete(module)
    elif op == 'add_member':
        body, changed, fail = add_member(module)
    elif op == 'remove_member':
        body, changed, fail = remove_member(module)
    else:
        return module.fail_json(msg="Unknown operation")

    module.exit_json(changed=changed, meta=body)

if __name__ == '__main__':
    main()
