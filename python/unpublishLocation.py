#!/usr/bin/env python3
""" """
import sys
import poms
import datetime

def usage():
    print(sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <program url>")

def main():
    NOW=datetime.datetime.utcnow()
    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, program_url = args

    poms.set_location(mid, program_url, publishStop = NOW)



if __name__ == "__main__":
    main()
