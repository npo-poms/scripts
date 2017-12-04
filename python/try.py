#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import poms
import xml.etree.ElementTree as ET




string = """
<program xmlns:media="urn:vpro:media:2009" xmlns:shared="urn:vpro:shared:2009" xmlns="urn:vpro:media:update:2009" type="CLIP" avType="VIDEO" embeddable="true">
<broadcaster>VPRO</broadcaster>
<title type="MAIN">Holland Doc</title>
<title type="SUB">Zwart ijs</title>
<title type="ORIGINAL">Holland Doc: Zwart IJs</title>
<description type="MAIN">Main title</description>
<description type="SHORT">Short title</description>
           <description type="EPISODE"> Documentaire over de band tussen het schaatsen op natuurijs en orthodox-christelijk Nederland. Zwart IJs volgt een aantal schaatsers in een jaar dat er bijna een Elfstedentocht kwam, op zondag.</description>
<tag>schaatsen</tag>
</program>
"""


xml = ET.fromstring(string)
print ET.dump(xml)

print xml.findall(pref + "title/[@type='MAIN']")[0].text
