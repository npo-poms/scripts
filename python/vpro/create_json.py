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
        split = file.stem.split('.', 2)
        profile = split[0] if len(split) == 2 else None
        
        if profile:
            not_in_api = directory + "/" + profile + ".not-in-api.data"
            not_in_sitemap = directory + "/" + profile + ".not-in-sitemap.data"
        else:
            not_in_api = None
            not_in_sitemap = None
        
        ob = {
           "file_name": file.name,
           "profile": profile,
           "svg": "plots/" + file.name,
           "not_in_api":  not_in_api if not_in_api and os.path.exists(not_in_api) else None,
           "not_in_sitemap":  not_in_sitemap if not_in_sitemap and os.path.exists(not_in_sitemap) else None

        }
        svgs.append(ob)

    
data = {
    "title": "Results of " + datetime.now().replace(microsecond=0).isoformat(),
    "svgs": svgs
}

with open(directory + '/data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
