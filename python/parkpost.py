#!/usr/bin/env python3
"""a"""
import sys
import poms
from xml.dom import minidom


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-s] [--resolvecrid] [-t <target>] <xml file>")

def main():
    opts,args = poms.opts(usage = usage, minargs = 1, args="t:e:srh")
    xml_file  = args[0]
    with open (xml_file, "r") as myfile:
        print poms.parkpost_str(myfile.read())


if __name__ == "__main__":
    main()
