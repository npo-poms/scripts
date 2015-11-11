#!/usr/bin/env python3
"""Script to move members of a group to a set of other groups"""

import sys
import poms

def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-s] [-t <target>] <MID> <NEWMID> [<NEWMID2>...]")

def move_to_group(item, group_mid, dest, position):
    mediaobject = item.childNodes[0]
    mid =  mediaobject.getAttribute("mid");
    print(mid + "->" + dest)
    if dest != group_mid:

        for memberOf in mediaobject.getElementsByTagName("memberOf"):
            print(memberOf.toxml())
            print(memberOf.firstChild.data)
            if memberOf.firstChild.data.startswith("urn:"):
                print("Error. Could not perform action because of MSE-2464. Need POMS 3.2")
                sys.exit(1)
            if memberOf.firstChild.data == group_mid:
                memberOf.firstChild.replaceWholeText(dest)
                print("->" + memberOf.firstChild.data)
                memberOf.setAttribute("position", str(position));
                break
        poms.post(mediaobject)

def main():
    opt, args = poms.opts(usage=usage, minargs=2)

    group_mid       = args[0]
    group_members   = poms.members(group_mid)
    dest_group_mids = args[1:]

    if len(group_members) == 0:
        print("The group " + group_mid + " has no members")

    # some math to distribute the objects as evenly as possible over the groups
    group_size = len(group_members) / len(dest_group_mids)
    remainder = len(group_members) % len(dest_group_mids)
    g = 0
    this_group_size = 0
    for m in group_members:
        move_to_group(m, group_mid, dest_group_mids[g], this_group_size + 1)
        this_group_size += 1
        maxsize = group_size + (1 if g < remainder else 0)
        if this_group_size >= maxsize:
            g += 1
            this_group_size = 0

if __name__ == "__main__":
    main()
