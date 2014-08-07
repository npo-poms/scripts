#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import poms
from xml.dom import minidom
import time


def main():
    opts,args = poms.opts()



    print "posting xml"
    mid = poms.post_str("""
    <program xmlns:media="urn:vpro:media:2009" xmlns:shared="urn:vpro:shared:2009" xmlns="urn:vpro:media:update:2009" type="CLIP" avType="VIDEO" embeddable="true">
    <broadcaster>VPRO</broadcaster>
    <title type="MAIN">Holland Doc</title>
    <title type="SUB">Zwart ijs</title>
    <title type="ORIGINAL">Holland Doc: Zwart IJs</title>
    <description type="MAIN">Main title</description>
    <description type="SHORT">Short title</description>
    <description type="EPISODE"> Documentaire over de band tussen het schaatsen op natuurijs en orthodox-christelijk Nederland. Zwart IJs volgt een aantal schaatsers in een jaar dat er bijna een Elfstedentocht kwam, op zondag.</description>
    <tag>geloof</tag>
    <tag>schaatsen</tag>
    <avAttributes>
    <avFileFormat>UNKNOWN</avFileFormat>
    <videoAttributes>
    <color>BLACK AND WHITE AND COLOR</color>
    </videoAttributes>
    <audioAttributes>
    <channels>2</channels>
    </audioAttributes>
    </avAttributes>
    <duration>P0DT1H35M0.000S</duration>
    <memberOf highlighted="false">urn:vpro:media:group:9707788</memberOf>
    <memberOf highlighted="false">urn:vpro:media:group:3126903</memberOf>
    <memberOf position="22" highlighted="false">urn:vpro:media:group:34376909</memberOf>
    <images>
    <image type="PICTURE" highlighted="false">
    <title>Zwart ijs</title>
    <description>Zwart ijs</description>
    <width>727</width>
    <height>409</height>
    <urn>urn:vpro:image:325587</urn>
    </image>
    </images>
    <segments/>
    </program>
    """);

    print mid

    time.sleep(5)

    print poms.get(mid).toprettyxml()

if __name__ == "__main__":
    main()
