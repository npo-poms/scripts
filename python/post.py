#!/usr/bin/env python
"""a"""
import sys
import poms
from xml.dom import minidom


def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-s] [-t <target>] <xml file>")

def main():
    opts,args = poms.opts(usage = usage, minargs = 1)
    xml_file  = args[0]
    with open (xml_file, "r") as myfile:
        print poms.post_str(myfile.read())


if __name__ == "__main__":
    main()
