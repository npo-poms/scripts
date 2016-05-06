#!/usr/bin/env python3
""" """
import sys
import poms
import xml.etree.ElementTree as ET

def usage():
    print(sys.argv[0] + " [-r] [-h] [-s] [-t <target>] <MID> <image file>")


if __name__ == "__main__":
    opt, args = poms.opts(usage = usage, minargs = 2)
    mid, duration = args
    xml = poms.get(mid, parser=ET)

    poms.xml_set_or_add_duration(xml, duration)

    print(ET.tostring(xml).decode("utf-8"))
    poms.post(xml)
