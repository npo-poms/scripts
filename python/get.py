#!/usr/bin/env python3
"""Get's and formats a POMS media update xml"""
import sys
import poms


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-t <target>] <MID>")

def main():
    opts, args = poms.opts(usage = usage, minargs = 1, args="t:srh")
    mid  = args[0]
    print(poms.get(mid).toprettyxml(encoding='utf-8', indent='  ').decode())


if __name__ == "__main__":
    main()
