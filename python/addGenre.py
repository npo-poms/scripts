#!/usr/bin/env python3
"""Script to add a genre to all members of a group. Supported in poms >= 3.2 only"""
import sys
import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <genreId>"

def main():

    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, genre_id = args

    for s in poms.members(mid):
        #print s.attributes['position'].value
        update     = s.getElementsByTagName('mediaUpdate')[0];
        member_mid = update.attributes['mid'].value

        print("Adding genre " + genre_id + " to " + member_mid);
        poms.add_genre(update, genre_id)
        poms.post(update)



if __name__ == "__main__":
    main()
