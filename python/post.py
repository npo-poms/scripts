#!/usr/bin/env python3
"""Posts a POMS media update XML"""
import sys
import poms
import codecs



def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-s] [--resolvecrid] [-t <target>] <xml file>")

if __name__ == "__main__":
    opts,args = poms.opts(usage = usage, minargs = 1, args="t:e:srh")
    xml_file  = args[0]
    with codecs.open(xml_file, "r", "utf-8") as myfile:
        print(poms.post_str(myfile.read()))
