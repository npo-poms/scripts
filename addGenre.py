#!/usr/bin/env python
"""Script to add a genre to all members of a group. Unfished as the POMS Rest service does not support this yet"""
import sys
import getopt
import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID>"

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],"t:srh")
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit(0)

    poms.credentials(opts)

    if len(args) == 0:
        usage()
        sys.exit(1)

    mid = args[0]

    for s in poms.members(mid):
        print s.attributes['position'].value
        update = s.getElementsByTagName('mediaUpdate')[0];
        print update.attributes['mid'].value

        print update.toxml()

    print "\n\nSadly we wan't edit genres by poms rest yet"
    sys.exit(1)


if __name__ == "__main__":
    main()
