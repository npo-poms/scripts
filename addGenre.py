#!/usr/bin/env python
"""Script to add a genre to all members of a group. Unfished as the POMS
   Rest service does not support this yet"""
import sys
import getopt
import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <genreId>"

def main():

    opt, args = poms.opts(usage = usage)

    if len(args) < 2:
        usage()
        sys.exit(1)

    mid = args[0]
    genreId = args[1]

    for s in poms.members(mid):
        #print s.attributes['position'].value
        update = s.getElementsByTagName('mediaUpdate')[0];
        mid = update.attributes['mid'].value

        print("Adding genre " + genreId + " to " + mid);
        poms.add_genre(update, genreId)
        poms.post(update)



if __name__ == "__main__":
    main()
