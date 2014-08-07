#!/usr/bin/env python
"""Get's and formats a POMS media update xml"""
import sys
import poms
from xml.dom import minidom


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-t <target>] <MID>")

def main():
    opts, args = poms.opts(usage = usage, minargs = 1, args="t:srh")
    mid  = args[0]
    print poms.get(mid).toprettyxml(encoding='utf-8', indent='  ')


if __name__ == "__main__":
    main()
