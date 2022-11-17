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
        
        txt_file = None
        if profile:
            if split[1] == 'not-in-api':
                txt_file =  "report." + profile + ".in_sitemap_but_not_in_api.txt"
            elif split[1] == 'not-in-sitemap':
                txt_file = "report." + profile + ".in_api_but_not_in_sitemap.txt"                
        
        ob = {
           "file_name": file.name,
           "profile": profile,
           "svg": "plots/" + file.name,
           "txt_file":  txt_file if txt_file and os.path.exists(directory + "/" + txt_file) else None,
        }
        svgs.append(ob)

    
data = {
    "title": "Results of " + datetime.now().replace(microsecond=0).isoformat(),
    "svgs": svgs
}

with open(directory + '/data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
