#!/usr/bin/env python

import urllib2
import sys
from xml.dom import minidom

import getopt

import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <NEWMID> [<NEWMID2>...]"
    poms.usage()

def movetogroup(item, groupMid, dest, position):
    mediaobject = item.childNodes[0]
    mid =  mediaobject.getAttribute("mid");
    print mid + "->" + dest
    if dest != groupMid:

        for memberOf in mediaobject.getElementsByTagName("memberOf"):
            print memberOf.toxml()
            print memberOf.firstChild.data
            if memberOf.firstChild.data == groupMid:
                memberOf.firstChild.replaceWholeText(dest)
                print "->" + memberOf.firstChild.data
                memberOf.setAttribute("position", str(position));
                break
        poms.post(mediaobject)




def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],"t:e:srh")
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit(0)

    poms.init(opts)

    if len(args) < 2:
        usage()
        sys.exit(1)


    groupMid       = args[0]
    groupMembers   = poms.members(groupMid)
    destGroupMids  = args[1:]

    # some math to distribute the objects as evenly as possible over the groups
    groupsize = len(groupMembers) / len(destGroupMids)
    remainder = len(groupMembers) % len(destGroupMids)
    g = 0
    thisgroupsize = 0
    for m in groupMembers:
        movetogroup(m, groupMid, destGroupMids[g], thisgroupsize + 1)
        thisgroupsize += 1
        maxsize = groupsize + (1 if g < remainder else 0)
        if thisgroupsize >= maxsize:
            g += 1
            thisgroupsize = 0



if __name__ == "__main__":
    main()
