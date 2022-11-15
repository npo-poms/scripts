#!/usr/bin/env python3

import json
import sys
import os
directory= sys.argv[1] if len(sys.argv) > 1 else "/home/michiel" 

svgs = []
for filename in os.listdir(directory + "/plots"):
    print(filename)
    ob = {
        "title": filename,
        "svg": "plots/" + filename
    }
    svgs.append(ob)

    
data = {
    "svgs": svgs
}

with open(directory + '/data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
