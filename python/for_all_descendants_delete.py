#!/usr/bin/env python3
"""Script to do something for all descendants of a poms group"""

from for_all_descendants import ForAllDescendants


class ForAllDescendantsDelete(ForAllDescendants):
    def __init__(self):
        super().__init__(processor = self.nope)
        self.description = "Delete"

    def do_one(self, member, idx):
        self.api.delete(member.mid)


if __name__ == "__main__":
    for_all = ForAllDescendantsDelete()
    for_all.command_line()
    for_all.main()



