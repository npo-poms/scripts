#!/usr/bin/env python
""" """
import sys
import poms

def usage():
    print sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <program url>"

def main():

    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, program_url = args

    poms.add_location(mid, program_url)



if __name__ == "__main__":
    main()
