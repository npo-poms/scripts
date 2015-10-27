#!/usr/bin/env python3
""" """
import sys
import poms

def usage():
    print(sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <program url>")

def main():

    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, program_url = args

    poms.post_location(mid, program_url)



if __name__ == "__main__":
    main()
