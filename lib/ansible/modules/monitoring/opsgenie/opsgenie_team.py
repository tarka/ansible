#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: 2019 Atlassian
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
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

'''

import base64
import json
import sys
from ansible.module_utils._text import to_text, to_bytes

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

REGION_URL = {
    'US': 'https://api.opsgenie.com/v2',
    'EU': 'https://api.eu.opsgenie.com/v2'
}


######################################################################
# Utils

def request(url, key, data=None, method=None):
    if data:
        data = json.dumps(data)

    response, info = fetch_url(module, url, data=data, method=method,
                               headers={'Content-Type': 'application/json',
                                        'Authorization': "GenieKey %s" % key})

    body = response and response.read()
    if body:
        return info, json.loads(to_text(body, errors='surrogate_or_strict'))
    else:
        return info, {}


def pfilter(params, keys):
    return { k: params[k]
             for k in keys
             if k in params and params[k]}


def statcheck(info, body):
    if info['status'] in (200, 201, 204):
        return body, True, None
    else:
        return body, False, info['msg']

def checkop(op, params, required):
    # Check we have the necessary per-operation parameters
    missing = []
    for parm in required[op]:
        if not params[parm]:
            missing.append(parm)
    if missing:
        module.fail_json(msg="Operation %s require the following missing parameters: %s" % (op, ",".join(missing)))


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


def create(base, key, params):
    # FIXME: Add members, or leave to individual calls?
    data = pfilter(params, ['name', 'description'])
    url = base + '/teams'
    info, body  = request(url, key, data=data, method='POST')

    if info['status'] == 409:
        # Conflict; assume team-name already exists
        return body, False, False
    else:
        return statcheck(info, body)


def delete(base, key, params):
    url = base + '/teams/' + params['name'] + '?identifierType=name'
    info, body  = request(url, key, method='DELETE')
    return statcheck(info, body)


def add_member(base, key, params):
    # TODO: Add always returns 'Added', even if the user was already
    # a member. Ideally we should check for this and quit with
    # changed=false.
    url = base + '/teams/' + params['name'] + '/members?teamIdentifierType=name'
    data = {
        'user': {
            'username': params['user']
        },
        'role': params['role']
    }

    info, body  = request(url, key, data=data, method='POST')

    return statcheck(info, body)


def remove_member(base, key, params):
    url = base + '/teams/' + params['name'] + '/members/' + params['user'] + '?teamIdentifierType=name'
    info, body  = request(url, key, method='DELETE')
    return statcheck(info, body)


def main():
    global module
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

    op = module.params['operation']
    key = module.params['key']
    region = module.params['region']
    base = REGION_URL[region]

    checkop(op, module.params, OP_REQUIRED)

    # Dispatch:
    # FIXME: This could be a getattr lookup, but it wasn't playing
    # well with the Ansible wrapper, so this works for now.
    if op == 'create':
        body, changed, fail = create(base, key, module.params)
    elif op == 'delete':
        body, changed, fail = delete(base, key, module.params)
    elif op == 'add_member':
        body, changed, fail = add_member(base, key, module.params)
    elif op == 'remove_member':
        body, changed, fail = remove_member(base, key, module.params)
    else:
        return module.fail_json(msg="Unknown operation")

    module.exit_json(changed=changed, meta=body)

if __name__ == '__main__':
    main()
