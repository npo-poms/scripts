#!/usr/bin/env python3
"""Script to do something for all descendants of a poms group"""

import pickle
import os
import sys
from tempfile import gettempdir

# some imports handy for the exec call
# noinspection PyUnresolvedReferences
import npoapi.xml.mediaupdate
# noinspection PyUnresolvedReferences
from dateutil.parser import parse
from npoapi import MediaBackend, MediaBackendUtil as MU



def init(processor=None, filter=None):
    global api
    api = MediaBackend().command_line_client()
    api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
    api.add_argument('-C', '--clean', action='store_true', default=False)
    api.add_argument('--dryrun', action='store_true', default=False)
    api.add_argument('--segments', action='store_true', default=False, help='')
    api.add_argument('--episodes', action='store_true', default=False, help='')
    api.add_argument('--include_self', action='store_true', default=False, help='')

    if filter is None:
        api.add_argument('--filter', type=str, help="""
Filter. A piece of python code to filter. E.g.
type(member) == npoapi.xml.mediaupdate.programUpdateType
member.type == 'CLIP'
'kort!' in short_title.lower()
""")


def main(processor=None, filter=None):

    args = api.parse_args()
    log = api.logger
    mid = args.mid[0]
    clean = args.clean


    tempfilename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    cache = os.path.join(gettempdir(), tempfilename + "." + mid + ".p")
    members = []
    if os.path.exists(cache) and not clean:
        log.info("Reusing from " + cache)
        members = pickle.load(open(cache, "rb"))
    else:
        if not clean:
            log.info("Not found " + cache)
        MU.descendants(api, mid, batch=200, target=members, segments=args.segments, episodes=args.episodes, log_progress=True)
        pickle.dump(members, open(cache, "wb"))

    log.info("Found " + str(len(members)) + " objects")
    deletes = 0


    for idx, member in enumerate(MU.iterate_objects(members)):
        member_mid = member.mid
        # noinspection PyUnusedLocal
        main_title = MU.title(member, "MAIN")
        # noinspection PyUnusedLocal
        short_title = MU.title(member, "SHORT")
        if filter:
            result = filter(member, idx)
            log.debug("%s Execed %s result %s", str(idx), str(filter), str(result))
            if not result:
                log.debug("Skipping %s, %s %s because of filter %s", str(type(member)), str(member.type) if hasattr(member, "type") else '?', member_mid, filter)
                continue

        if not args.dryrun:
            log.info("%s Deleting %s", str(idx), member_mid)
            api.delete(member_mid)
        else:
            log.info("%s Dry run deleting %s", str(idx), member_mid)

        deletes += 1

    if args.include_self:
        if not args.dryrun:
            log.info("Deleting %s", mid)
            api.delete(mid)
        else:
            log.info("Dry run deleting %s", mid)
        deletes += 1

    log.info("Ready. Deleted %s object from POMS", str(deletes))


if __name__ == "__main__":
    init()
    main()



