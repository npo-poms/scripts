#!/usr/bin/env python3
"""Get's and formats a POMS media update xml"""
import sys
import poms


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-t <target>] <MID>")


if __name__ == "__main__":
    opts, args = poms.opts(usage=usage, minargs=1, args="t:srh")
    mid = args[0]
    print(poms.members(mid))
