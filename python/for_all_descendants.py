#!/usr/bin/env python3
"""Script to do something for all descendants of a poms group"""

import pickle
import os
import npoapi.xml.mediaupdate
from dateutil.parser import parse
from npoapi import MediaBackend, MediaBackendUtil as MU

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('process', type=str, nargs=1, help="""
python code to postprocess. E.g.
member.genre.append('1.3.4')
MSE-3554

""")
api.add_argument('-C', '--clean', action='store_true', default=False, help='clean build')
api.add_argument('--filter', type=str, help="""
Filter. A piece of python code to filter. E.g. "type(member) ==  npoapi.xml.mediaupdate.programUpdateType"
""")
args = api.parse_args()
process = args.process[0]
mid = args.mid[0]
filter = args.filter
clean = args.clean

cache = "/tmp/foralldescendants.p"
members = []
if os.path.exists(cache) and not clean:
    api.logger.info("Reusing from " + cache)
    members = pickle.load(open(cache, "rb"))
else:
    MU.descendants(api, mid, batch=200, target=members, segments=False, episodes=False, log_progress=True)
    pickle.dump(members, open(cache, "wb"))

api.logger.info("Found " + str(len(members)) + " objects")


for idx, member in enumerate(MU.iterate_objects(members)):
    member_mid = member.mid
    if filter:
        result = eval(filter)
        api.logger.debug("Execed %s result %s", str(filter), str(result))
        if not result:
            api.logger.info("Skipping %s, %s %s because of filter %s", str(type(member)), str(member.type), member_mid,
                            filter)
            continue
    exec(process)
    api.logger.info("Found " + member_mid)
    api.logger.debug("Execed " + process)
    api.post(member)


