#!/usr/bin/env python3
"""Get's and formats a POMS media update xml"""
import sys
import poms
from xml.dom import minidom
import xml.etree.ElementTree as ET

def usage():
    print(sys.argv[0] +
          " [-r] [-h] [-t <target>] <MID> [<xpath>] [<attr>]")


if __name__ == "__main__":
    opts, args = poms.opts(usage = usage, minargs = 1, args="t:srh")
    mid  = args[0]
    xpath = None
    if len(args) > 1:
        xpath = args[1]

    xml = None
    if xpath:
        attr = None
        if len(args) > 2:
            attr = args[2]
        xml = poms.get(mid, parser=ET)
        result = xml.findall(xpath, poms.namespaces)
        for el in result:
            if attr:
                print(el.get(attr))
            else:
                print(el.text)

    else:
        xml = poms.get(mid)
        if xml:
            #print(ET.tostring(xml).decode("utf-8"))
            print(xml.toprettyxml(encoding='utf-8', indent='  ').decode(sys.stdout.encoding, "surrogateescape"))
        else:
            print("<empty />")
