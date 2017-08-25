#!/usr/bin/env python3

import requests

resp  = requests.head("http://www.vpro.nl", allow_redirects=False)

print(resp.status_code)
