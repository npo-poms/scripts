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



class ForAllDescendants:

    def __init__(self, mid = None, clean=False, segments=False, episodes=False, filter=None, dryrun=False, include_self=False, processor = None):

        self.api = MediaBackend().command_line_client()
        self.description = "Doing for all"
        self.clean = clean
        self.segments = segments
        self.episodes = episodes
        self.filter = filter
        self.dryrun = dryrun
        self.include_self = include_self
        self.mid = mid
        self.logger = self.api.logger
        self.processor = processor


    def command_line(self):
        api = self.api

        api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
        api.add_argument('-C', '--clean', action='store_true', default=False)
        api.add_argument('--dryrun', action='store_true', default=False)
        api.add_argument('--segments', action='store_true', default=False, help='')
        api.add_argument('--episodes', action='store_true', default=False, help='')
        api.add_argument('--include_self', action='store_true', default=False, help='')
        if self.processor is None:
            api.add_argument('process', type=str, nargs=1, help=
            """
python code to postprocess. E.g.

member.genre.append('1.3.4')

member.publishStop=parse("2018-12-31")

""")
        if self.filter is None:
            api.add_argument('--filter', type=str, help="""
    Filter. A piece of python code to filter. E.g.
    type(member) == npoapi.xml.mediaupdate.programUpdateType
    member.type == 'CLIP'
    'kort!' in short_title.lower()
    """)

    def parse_args(self):
        args = self.api.parse_args()

        self.processor = self.function_or_arg(self.processor, args, "process", self.logger)
        self.filter = self.function_or_arg(self.filter, args, "filter", self.logger)
        self.mid = args.mid[0]
        self.clean = args.clean or self.clean
        self.segments = args.segments or self.segments
        self.episodes = args.episodes or self.episodes
        self.dryrun = args.dryrun or self.dryrun
        self.include_self = args.include_self or self.include_self

    def do_one(self, member, idx):
        self.api.post(member)


    def do_all(self):
        log = self.api.logger
        tempfilename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        cache = os.path.join(gettempdir(), tempfilename + "." + self.mid + ".p")
        members = []
        if os.path.exists(cache) and not self.clean:
            log.info("Reusing from " + cache)
            members = pickle.load(open(cache, "rb"))
        else:
            if not self.clean:
                log.info("Not found " + cache)
            MU.descendants(self.api, self.mid, batch=200, target=members, segments=self.segments, episodes=self.episodes,
                           log_progress=True)
            pickle.dump(members, open(cache, "wb"))

        log.info("Found " + str(len(members)) + " objects")
        count = 0

        for idx, member in enumerate(MU.iterate_objects(members)):
            member_mid = member.mid
            # noinspection PyUnusedLocal
            main_title = MU.title(member, "MAIN")
            # noinspection PyUnusedLocal
            short_title = MU.title(member, "SHORT")
            if self.filter:
                result = self.filter(member, idx)
                log.debug("%s Execed %s result %s", str(idx), str(self.filter), str(result))
                if not result:
                    log.debug("Skipping %s, %s %s because of filter %s", str(type(member)),
                              str(member.type) if hasattr(member, "type") else '?', member_mid, self.filter)
                    continue

            self.processor(member, idx)
            if not self.dryrun:
                log.info("%s %s %s", str(idx), self.description, member_mid)
                self.do_one(member, idx)
            else:
                log.info("%s Dry run %s %s", str(idx), self.description, member_mid)

            count += 1

        if self.include_self:
            if not self.dryrun:
                log.info("Deleting %s", self.mid)
                self.do_one(self.api.get(self.mid), None)
            else:
                log.info("Dry run deleting %s", self.mid)
            count += 1

        log.info("Ready. %s %s object from POMS", self.description, str(count))
        return count

    def function_or_arg(self, given_function, args, attr, log):
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

    def nope(self, *args):
        """"""

    def main(self):
        self.parse_args()
        self.do_all()



if __name__ == "__main__":
    for_all = ForAllDescendants()
    for_all.command_line()
    for_all.main()




