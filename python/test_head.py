#!/usr/bin/env python3

import requests

try:
    resp  = requests.head("http://www.vaprddddo.nl", allow_redirects=False)
    print(resp.status_code)
catch:
    print("HOI")
