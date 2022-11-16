#!/usr/bin/env python3

import json
import sys
import os
from pathlib import Path

from datetime import datetime

directory= sys.argv[1] if len(sys.argv) > 1 else "/home/michiel" 

svgs = []
files = sorted(Path(directory + "/plots").iterdir(), key=os.path.getmtime, reverse=True)
for file in files:
    if file.suffix == '.svg': 
        print(file.name)
        ob = {
           "title": file.name,
           "svg": "plots/" + file.name
        }
        svgs.append(ob)

    
data = {
    "title": "Results of " + datetime.now().replace(microsecond=0).isoformat(),
    "svgs": svgs
}

with open(directory + '/data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
