#!/usr/bin/env python3
"""Script to do delete all descendants of a poms group"""

#  ./for_all_descendants_set_embargo.py -e test --segments --episodes --recurse VPWON_1305978 '' '2022-02-07T12:00:00Z'
from datetime import datetime

import dateutil.parser
import pytz
from npoapi.base import Binding
from npoapi.xml.media import platformTypeEnum

from for_all_descendants import ForAllDescendants


class ForAllDescendantsSetEmbargo(ForAllDescendants):
    def __init__(self, **kwargs):
        super().__init__(processor = self.nope, binding=Binding.PYXB, **kwargs)
        self.description = "Set embargo"
        self.processor_description = "Set embargo"


    def command_line(self):
        super().command_line()
        self.api.add_argument("start", type=str, nargs=1, help='embargo start')
        self.api.add_argument("stop", type=str, nargs=1, help='embargo stop')
        self.api.add_argument('--locations', action='store_true', default=False)


    def parse_args(self):
        super().parse_args()
        args = self.api.parse_args()
        self.start = args.start[0].replace("'", '')
        self.stop = args.stop[0].replace("'", '')
        self.locations = args.locations


    def do_one(self, member, idx):
        if self.locations:
            for l in member.prediction:
                if l.value() == platformTypeEnum.INTERNETVOD:
                    self.logger.info("%s (%s %s)" % (l, l.publishStart, l.publishStop))
                    if self.start != '':
                        l.publishStart = self.start
                    if self.stop != '':
                        l.publishStop = dateutil.parser.parse(self.stop)
        else:
            if self.start != '':
                member.publishStart = self.start
            if self.stop != '':
                member.publishStop = dateutil.parser.parse(self.stop)

        if member.scheduleEvents:
            for s in member.scheduleEvents.scheduleEvent:
                # We seem to hit a bug in pyxb, local dates are unmarshalled to somethign it can't marshall again
                #s.guideDay = datetime.date.fromtimestamp(s.guideDay)
                self.logger.debug("Setting guideday %s to None" % s.guideDay)
                s.guideDay = None


        self.logger.info("%s" % member.mid)
        self.api.post(member)


if __name__ == "__main__":
    ForAllDescendantsSetEmbargo().main()



