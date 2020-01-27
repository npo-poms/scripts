#!/usr/bin/env python3
"""Script to do delete all descendants of a poms group"""

import dateutil.parser

from for_all_descendants import ForAllDescendants


class ForAllDescendantsSetEmbargo(ForAllDescendants):
    def __init__(self, **kwargs):
        super().__init__(processor = self.nope, **kwargs)
        self.description = "Set embargo"
        self.processor_description = "Set embargo"


    def command_line(self):
        super().command_line()
        self.api.add_argument("start", type=str, nargs=1, help='embargo start')
        self.api.add_argument("stop", type=str, nargs=1, help='embargo stop')


    def parse_args(self):
        super().parse_args()
        args = self.api.parse_args()
        self.start = args.start[0].replace("'", '')
        self.stop = args.stop[0].replace("'", '')


    def do_one(self, member, idx):
        if self.start != '':
            member.publishStart = self.start
        if self.stop != '':
            member.publishStop = dateutil.parser.parse(self.stop)
        self.api.post(member)


if __name__ == "__main__":
    ForAllDescendantsSetEmbargo().main()



