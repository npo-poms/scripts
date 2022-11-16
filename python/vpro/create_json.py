#!/usr/bin/env python3

import json
import sys
import os
from datetime import datetime

directory= sys.argv[1] if len(sys.argv) > 1 else "/home/michiel" 

svgs = []
os.chdir(directory)
files = sorted(filter(os.path.isfile, os.listdir('./plots')), key=os.path.getmtime, reverse=True)
for filename in files:
    print(filename)
    ob = {
        "title": filename,
        "svg": "plots/" + filename
    }
    svgs.append(ob)

    
data = {
    "title": "Results of " + datetime.now().replace(microsecond=0).isoformat(),
    "svgs": svgs
}

with open(directory + '/data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
