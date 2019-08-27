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
    choices: [ create, update, delete ]
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

  members:
    required: false
    description:
      - An optional list of team-member usernames for the create/update operations.

notes:
    - 
'''

EXAMPLES = '''

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


def request(url, key, data=None, method=None):
    if data:
        data = json.dumps(data)

    response, info = fetch_url(module, url, data=data, method=method,
                               headers={'Content-Type': 'application/json',
                                        'Authorization': "GenieKey %s" % key})
    status = info['status']

    body = response and response.read()
    if body:
        return status, json.loads(to_text(body, errors='surrogate_or_strict'))
    else:
        return status, {}


def pfilter(params, keys):
    return { k: params[k]
             for k in keys
             if k in params and params[k]}


def create(base, key, params):
    # FIXME: Add members, or leave to individual calls?
    data = pfilter(params, ['name', 'description'])
    url = base + '/teams'
    stat, body  = request(url, key, data=data, method='POST')

    if stat in (200, 201, 204):
        return body, True, False
    elif stat == 409:
        # Conflict; assume team-name already exists
        return body, False, False
    else:
        return body, False, True


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            operation=dict(choices=['create', 'update', 'delete'],
                           aliases=['command'], required=True),
            key=dict(aliases=['apikey'], required=True, no_log=True),
            region=dict(required=False, default='US'),

            name=dict(required=True),
            description=dict(required=False),
        ),
        supports_check_mode=False
    )

    op = module.params['operation']
    key = module.params['key']
    region = module.params['region']
    base = REGION_URL[region]

    # Dispatch
    try:
        # Lookup the corresponding method for this operation. This is
        # safe as the AnsibleModule should remove any unknown
        # operations. Each op should take a base URL, key and the
        # params. It should return (body, changed, failed).
        thismod = sys.modules[__name__]
        func = getattr(thismod, op)

        ret, changed, fail = func(base, key, module.params)

        if fail:
            module.fail_json(body)


    except Exception as e:
        return module.fail_json(msg=e.message)

    module.exit_json(changed=changed, meta=ret)

if __name__ == '__main__':
    main()
