#!/usr/bin/env python3
"""Script to add a genre to all members of a group. Supported in poms >= 3.2 only"""
import sys
import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <genreId>"

def main():

    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, genre_id = args

    update = poms.get(mid)

    print("Adding genre " + genre_id + " to " + mid);
    poms.add_genre(update, genre_id)
    poms.post(update)



if __name__ == "__main__":
    main()
