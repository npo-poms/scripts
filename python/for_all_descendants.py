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

def function_or_arg(given_function, args, attr, log):
    if given_function is None:
        to_exec = getattr(args, attr)
        if type(to_exec) == list:
            to_exec = to_exec[0]
        if not to_exec is None:
            if os.path.exists(to_exec):
                log.info("%s is a file.", str(to_exec))
                to_exec = open(to_exec).read()

            def exec_string(member, idx):
                exec(to_exec)

            given_function = exec_string

        else:
            given_function = None
    return given_function




def init(processor=None, filter=None):
    global api
    api = MediaBackend().command_line_client()
    api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')

    if processor is None:
        api.add_argument('process', type=str, nargs=1, help="""
    python code to postprocess. E.g.

member.genre.append('1.3.4')

member.publishStop=parse("2018-12-31")

""")
    api.add_argument('-C', '--clean', action='store_true', default=False)
    api.add_argument('--dryrun', action='store_true', default=False)

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
    processor = function_or_arg(processor, args, "process", log)
    mid = args.mid[0]

    filter = function_or_arg(filter, args, "filter", log)
    clean = args.clean

    log = api.logger


    tempfilename = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    cache = os.path.join(gettempdir(), tempfilename + "." + mid + ".p")
    members = []
    if os.path.exists(cache) and not clean:
        log.info("Reusing from " + cache)
        members = pickle.load(open(cache, "rb"))
    else:
        if not clean:
            log.info("Not found " + cache)
        MU.descendants(api, mid, batch=200, target=members, segments=False, episodes=False, log_progress=True)
        pickle.dump(members, open(cache, "wb"))

    log.info("Found " + str(len(members)) + " objects")
    posts = 0


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

        processor(member, idx)

        if not args.dryrun:
            log.info("%s Execed %s for %s and posting", str(idx), processor, member_mid)
            api.post(member)
        else:
            log.info("%s Execed %s for %s (not posting because of dryrun parameter)", str(idx), processor, member_mid)

        posts += 1

    log.info("Ready. Posted %s updates to POMS", str(posts))


if __name__ == "__main__":
    init()
    main()



