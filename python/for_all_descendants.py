#!/usr/bin/env python3
"""Script to do something for all descendants of a poms group"""

import pickle
import os
# some imports handy for the exec call
import npoapi.xml.mediaupdate
from dateutil.parser import parse
from npoapi import MediaBackend, MediaBackendUtil as MU

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('process', type=str, nargs=1, help="""
python code to postprocess. E.g.

member.genre.append('1.3.4')

member.publishStop=parse("2018-12-31")

""")
api.add_argument('-C', '--clean', action='store_true', default=False)
api.add_argument('--dryrun', action='store_true', default=False)

api.add_argument('--filter', type=str, help="""
Filter. A piece of python code to filter. E.g.
type(member) == npoapi.xml.mediaupdate.programUpdateType
member.type == 'CLIP'
member.mainTti
""")
args = api.parse_args()
process = args.process[0]
mid = args.mid[0]
filter = args.filter
clean = args.clean

log = api.logger

cache = "/tmp/foralldescendants.p"
members = []
if os.path.exists(cache) and not clean:
    log.info("Reusing from " + cache)
    members = pickle.load(open(cache, "rb"))
else:
    MU.descendants(api, mid, batch=200, target=members, segments=False, episodes=False, log_progress=True)
    pickle.dump(members, open(cache, "wb"))

log.info("Found " + str(len(members)) + " objects")
posts = 0

for idx, member in enumerate(MU.iterate_objects(members)):
    member_mid = member.mid
    main_title = MU.title(member, "MAIN")
    short_title = MU.title(member, "SHORT")
    if filter:
        result = eval(filter)
        log.debug("Execed %s result %s", str(filter), str(result))
        if not result:
            log.debug("Skipping %s, %s %s because of filter %s", str(type(member)), str(member.type), member_mid,
                            filter)
            continue
    if os.path.exists(process):
        log.info("%s is a file.", str(process))
        exec(open(process).read())
    else:
        exec(process)
    log.info("Execed %s for %s", process, member_mid)
    if not args.dryrun:
        api.post(member)
    posts += 1

log.info("Ready. Posted %s updates to POMS", str(posts))




