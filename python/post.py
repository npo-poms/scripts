#!/usr/bin/env python3
"""Posts a POMS media update XML"""
import sys
import poms


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-s] [--resolvecrid] [-t <target>] <xml file>")

def main():
    opts,args = poms.opts(usage = usage, minargs = 1, args="t:e:srh")
    xml_file  = args[0]
    with open (xml_file, "r") as myfile:
        print(poms.post_str(myfile.read()))


if __name__ == "__main__":
    main()
