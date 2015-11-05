#!/usr/bin/env python3
"""Get's and formats a POMS media update xml"""
import sys
import poms
from xml.dom import minidom
import xml.etree.ElementTree as ET

def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-t <target>] <MID>")

def main():
    opts, args = poms.opts(usage = usage, minargs = 1, args="t:srh")
    mid  = args[0]
    namespaces = {'update': 'urn:vpro:media:update:2009'}
    #print(poms.get(mid, parser=minidom).toprettyxml(encoding='utf-8', indent='  ').decode(sys.stdout.encoding, "surrogateescape"))
    print(poms.get(mid, parser=ET).findall("update:title[1]", namespaces)[0].text)


if __name__ == "__main__":
    main()
