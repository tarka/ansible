# -*- coding: utf-8 -*-

# Copyright: 2019 Atlassian
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import sys
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import fetch_url

REGION_URL = {
    'US': 'https://api.opsgenie.com/v2',
    'EU': 'https://api.eu.opsgenie.com/v2'
}

def request(module, endpoint, data=None, method=None):
    base = REGION_URL[module.params['region']]
    url = base+endpoint
    key = module.params['key']

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

def checkop(module, required):
    # Check we have the necessary per-operation parameters
    op = module.params['operation']
    missing = []
    for parm in required[op]:
        if not module.params[parm]:
            missing.append(parm)
    if missing:
        module.fail_json(msg="Operation %s require the following missing parameters: %s" % (op, ",".join(missing)))

