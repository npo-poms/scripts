#!/usr/bin/env python3
"""Script to do delete all descendants of a poms group"""

from for_all_descendants import ForAllDescendants


class ForAllDescendantsDelete(ForAllDescendants):
    def __init__(self, **kwargs):
        super().__init__(processor = self.nope, **kwargs)
        self.description = "Delete"

    def do_one(self, member, idx):
        print(member.locations.location[0].programUrl)
        self.api.delete(member.mid)


if __name__ == "__main__":
    ForAllDescendantsDelete().main()



